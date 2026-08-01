// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 17:22:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Native Alert Center fallback for local ack action drain. */
class AlertCenterActivity : Activity() {
    private lateinit var summary: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Alert Center"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        summary = TextView(this).apply {
            text = "Local alert actions ready to drain"
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val drain = Button(this).apply {
            text = "Drain alert ack actions"
            setOnClickListener { drainAlertActions() }
        }
        layout.addView(title)
        layout.addView(summary)
        layout.addView(drain)
        setContentView(layout)
    }

    private fun drainAlertActions() {
        summary.text = "Draining alert ack actions..."
        Thread {
            val settings = ApiSettingsStore(this)
            val session = SecureSessionStore(this).load()
            if (session == null) {
                runOnUiThread { summary.text = "No session; cannot ack alerts" }
                return@Thread
            }
            val result = AlertAckDrainer(
                this,
                NativeApiClient(settings.baseUrl(), session.accessToken),
                ackBy = session.userId,
                deviceId = session.deviceId,
            ).drain()
            runOnUiThread {
                summary.text = "acked=${result.succeeded} failed=${result.failed}"
            }
        }.start()
    }
}
