// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 04:45:00

package com.aiparentingcopilot

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Android Keystore-backed session token store.
 *
 * Stores only the encrypted access token plus non-secret identifiers needed to
 * restore app session. The AES key is non-exportable from Android Keystore.
 */
class SecureSessionStore(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun save(session: NativeSession) {
        val encrypted = encrypt(session.accessToken)
        prefs.edit()
            .putString("token_ciphertext", encrypted.ciphertext)
            .putString("token_iv", encrypted.iv)
            .putString("family_id", session.familyId)
            .putString("user_id", session.userId)
            .putString("baby_id", session.babyId)
            .putString("device_id", session.deviceId)
            .putString("role", session.role)
            .apply()
    }

    fun load(): NativeSession? {
        val ciphertext = prefs.getString("token_ciphertext", null) ?: return null
        val iv = prefs.getString("token_iv", null) ?: return null
        return NativeSession(
            accessToken = decrypt(EncryptedValue(ciphertext, iv)),
            familyId = prefs.getString("family_id", null) ?: return null,
            userId = prefs.getString("user_id", null) ?: return null,
            babyId = prefs.getString("baby_id", null),
            deviceId = prefs.getString("device_id", null),
            role = prefs.getString("role", null),
        )
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    private fun encrypt(plainText: String): EncryptedValue {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        val ciphertext = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
        return EncryptedValue(
            ciphertext = Base64.encodeToString(ciphertext, Base64.NO_WRAP),
            iv = Base64.encodeToString(cipher.iv, Base64.NO_WRAP),
        )
    }

    private fun decrypt(value: EncryptedValue): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        val iv = Base64.decode(value.iv, Base64.NO_WRAP)
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv))
        val bytes = cipher.doFinal(Base64.decode(value.ciphertext, Base64.NO_WRAP))
        return String(bytes, Charsets.UTF_8)
    }

    private fun getOrCreateKey(): SecretKey {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        keyStore.getKey(KEY_ALIAS, null)?.let { return it as SecretKey }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build(),
        )
        return generator.generateKey()
    }

    companion object {
        private const val PREFS = "parenting_secure_session"
        private const val KEY_ALIAS = "ai_parenting_copilot_session_key"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_LENGTH_BITS = 128
    }
}

data class NativeSession(
    val accessToken: String,
    val familyId: String,
    val userId: String,
    val babyId: String? = null,
    val deviceId: String? = null,
    val role: String? = null,
)

data class EncryptedValue(val ciphertext: String, val iv: String)
