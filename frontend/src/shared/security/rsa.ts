import forge from "node-forge"

/**
 * RSA-OAEP-SHA256 浏览器加密工具。
 *
 * 优先使用原生 Web Crypto；通过局域网 HTTP 地址访问（例如
 * http://172.16.10.61:5173）时，部分浏览器会禁用 crypto.subtle，
 * 此时使用 node-forge 的纯 JavaScript 实现兜底，保持与后端相同的
 * RSA-OAEP-SHA256 算法和密文格式。
 */

function pemToDer(publicKeyPem: string): ArrayBuffer {
  const base64 = publicKeyPem
    .replace("-----BEGIN PUBLIC KEY-----", "")
    .replace("-----END PUBLIC KEY-----", "")
    .replace(/\s/g, "")

  if (!base64) {
    throw new Error("加密公钥为空")
  }

  let binary: string
  try {
    binary = atob(base64)
  } catch (error) {
    throw new Error("加密公钥格式无效", { cause: error })
  }

  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return bytes.buffer
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = ""
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }
  return btoa(binary)
}

export async function encryptWithRsaPublicKey(publicKeyPem: string, plaintext: string): Promise<string> {
  if (!plaintext) {
    throw new Error("密码不能为空")
  }

  const webCrypto = globalThis.crypto
  if (webCrypto?.subtle) {
    try {
      const key = await webCrypto.subtle.importKey(
        "spki",
        pemToDer(publicKeyPem),
        { name: "RSA-OAEP", hash: "SHA-256" },
        false,
        ["encrypt"],
      )
      const encrypted = await webCrypto.subtle.encrypt(
        { name: "RSA-OAEP" },
        key,
        new TextEncoder().encode(plaintext),
      )
      return bytesToBase64(new Uint8Array(encrypted))
    } catch {
      // 部分 WebView 暴露 crypto.subtle 但实际不支持 RSA-OAEP，继续走兼容实现。
    }
  }

  return encryptWithForge(publicKeyPem, plaintext)
}

function encryptWithForge(publicKeyPem: string, plaintext: string): string {
  try {
    const publicKey = forge.pki.publicKeyFromPem(publicKeyPem)
    const encrypted = publicKey.encrypt(
      forge.util.encodeUtf8(plaintext),
      "RSA-OAEP",
      {
        md: forge.md.sha256.create(),
        mgf1: { md: forge.md.sha256.create() },
      },
    )
    return forge.util.encode64(encrypted)
  } catch (error) {
    throw new Error("当前浏览器无法完成 RSA-OAEP-SHA256 加密，请改用 HTTPS 或更新浏览器。", { cause: error })
  }
}
