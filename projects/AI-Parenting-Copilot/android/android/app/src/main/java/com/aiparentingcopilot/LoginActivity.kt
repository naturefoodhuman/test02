// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 20:05:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject

/** Native login fallback that stores tokens via Android Keystore. */
class LoginActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var apiBaseUrl: EditText
    private lateinit var familyId: EditText
    private lateinit var displayName: EditText
    private lateinit var secret: EditText
    private lateinit var babyId: EditText

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val settings = ApiSettingsStore(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Login"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        apiBaseUrl = EditText(this).apply {
            hint = ApiSettingsStore.DEFAULT_EMULATOR_API
            setText(settings.baseUrl())
        }
        familyId = EditText(this).apply { hint = "family_id" }
        displayName = EditText(this).apply { hint = "display name" }
        secret = EditText(this).apply { hint = "secret" }
        babyId = EditText(this).apply { hint = "baby_id (optional)" }
        status = TextView(this).apply {
            text = "Not logged in"
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val login = Button(this).apply {
            text = "Login and register phone"
            setOnClickListener { loginAndStore() }
        }
        val clear = Button(this).apply {
            text = "Clear session"
            setOnClickListener {
                SecureSessionStore(this@LoginActivity).clear()
                status.text = "Session cleared"
            }
        }
        layout.addView(title)
        layout.addView(apiBaseUrl)
        layout.addView(familyId)
        layout.addView(displayName)
        layout.addView(secret)
        layout.addView(babyId)
        layout.addView(login)
        layout.addView(clear)
        layout.addView(status)
        setContentView(layout)
    }

    private fun loginAndStore() {
        status.text = "Logging in..."
        Thread {
            val settings = ApiSettingsStore(this)
            settings.setBaseUrl(apiBaseUrl.text.toString())
            val baseUrl = settings.baseUrl()
            val loginBody = JSONObject()
                .put("family_id", familyId.text.toString())
                .put("display_name", displayName.text.toString())
                .put("secret", secret.text.toString())
                .toString()
            val loginResult = NativeApiClient(baseUrl).postJsonResult("/api/v1/auth/login", loginBody)
            if (loginResult.statusCode !in 200..299) {
                runOnUiThread { status.text = "login failed=${loginResult.statusCode}" }
                return@Thread
            }
            val loginJson = JSONObject(loginResult.body)
            val token = loginJson.getString("access_token")
            var session = NativeSession(
                accessToken = token,
                familyId = loginJson.getString("family_id"),
                userId = loginJson.getString("user_id"),
                babyId = babyId.text.toString().ifBlank { null },
                deviceId = loginJson.optString("device_id").ifBlank { null },
                role = loginJson.optString("role").ifBlank { null },
            )
            val registerBody = JSONObject()
                .put("kind", "phone")
                .put("name", "Android native shell")
                .toString()
            val registerResult = NativeApiClient(baseUrl, token)
                .postJsonResult("/api/v1/auth/devices/register", registerBody)
            if (registerResult.statusCode in 200..299) {
                val deviceId = JSONObject(registerResult.body).optString("device_id").ifBlank { null }
                session = session.copy(deviceId = deviceId)
            }
            SecureSessionStore(this).save(session)
            runOnUiThread {
                status.text = "login=${loginResult.statusCode} device=${registerResult.statusCode}"
            }
        }.start()
    }
}
