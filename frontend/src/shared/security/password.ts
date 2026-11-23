import { getEncryptionPublicKey } from "@/shared/api/security"

import { encryptWithRsaPublicKey } from "./rsa"

/** Encrypt a page password before it enters an API request body. */
export async function encryptPassword(password: string): Promise<string> {
  const key = await getEncryptionPublicKey()
  if (key.algorithm !== "RSA-OAEP-SHA256") {
    throw new Error("后端返回了不受支持的密码加密算法")
  }
  return encryptWithRsaPublicKey(key.public_key, password)
}
