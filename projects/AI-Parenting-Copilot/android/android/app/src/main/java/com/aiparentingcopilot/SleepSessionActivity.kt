// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 19:29:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject

/** Native Sleep Session fallback for toolchain/device smoke. */
class SleepSessionActivity : Activity() {
    private lateinit var status: TextView
    private var sessionId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Sleep Session"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        status = TextView(this).apply {
            text = "Ready"
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val start = Button(this).apply {
            text = "Start sleep session"
            setOnClickListener { startSleepSession() }
        }
        val pause = Button(this).apply {
            text = "Pause"
            setOnClickListener { postSessionAction("pause") }
        }
        val resume = Button(this).apply {
            text = "Resume"
            setOnClickListener { postSessionAction("resume") }
        }
        val end = Button(this).apply {
            text = "End"
            setOnClickListener { postSessionAction("end") }
        }
        layout.addView(title)
        layout.addView(status)
        layout.addView(start)
        layout.addView(pause)
        layout.addView(resume)
        layout.addView(end)
        setContentView(layout)
    }

    private fun startSleepSession() {
        status.text = "Starting..."
        Thread {
            val settings = ApiSettingsStore(this)
            val session = SecureSessionStore(this).load()
            val body = JSONObject()
                .put("baby_id", session?.babyId ?: QuickRecordActivity.DEV_BABY_ID)
                .put("family_id", session?.familyId ?: QuickRecordActivity.DEV_FAMILY_ID)
                .toString()
            val result = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .postJsonResult("/api/v1/sleep-sessions", body)
            sessionId = Regex("\"id\"\\s*:\\s*\"([^\"]+)\"").find(result.body)?.groupValues?.get(1)
            runOnUiThread { status.text = "start status=${result.statusCode} session=${sessionId ?: "?"}" }
        }.start()
    }

    private fun postSessionAction(action: String) {
        val id = sessionId ?: return
        status.text = "$action..."
        Thread {
            val settings = ApiSettingsStore(this)
            val session = SecureSessionStore(this).load()
            val code = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .postJson("/api/v1/sleep-sessions/$id/$action", "{}")
            runOnUiThread { status.text = "$action status=$code" }
        }.start()
    }
}
