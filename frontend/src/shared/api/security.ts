import { request } from "./http"

export interface EncryptionPublicKey {
  algorithm: "RSA-OAEP-SHA256"
  public_key: string
}

/**
 * 获取浏览器加密页面密码所需的 RSA 公钥。
 * 用途：为后续密码提交准备公钥，不返回私钥或可恢复的秘密。
 * 请求：GET /v1/security/public-key/（统一客户端拼接 /api）；无请求参数；公开、幂等。
 * 响应：返回 EncryptionPublicKey，algorithm 为 RSA-OAEP-SHA256，public_key 为 PEM 字符串。
 * 错误：CRYPTO_NOT_CONFIGURED 或统一网络错误；统一客户端保留 X-Trace-ID，页面只展示安全提示。
 * 兼容性：算法标识和密钥格式属于契约字段，算法轮换必须先增加版本并保留迁移期。
 */
export function getEncryptionPublicKey(): Promise<EncryptionPublicKey> {
  return request<EncryptionPublicKey>({
    method: "GET",
    url: "/v1/security/public-key/",
  })
}
