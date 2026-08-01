// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 17:23:00

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
        layout.addView(title)
        layout.addView(status)
        layout.addView(start)
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
            val code = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .postJson("/api/v1/sleep-sessions", body)
            runOnUiThread { status.text = "start status=$code" }
        }.start()
    }
}
