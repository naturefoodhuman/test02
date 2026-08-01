// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 19:28:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Native Alert Center fallback for server alert list and local ack action drain. */
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
        val refresh = Button(this).apply {
            text = "Refresh server alerts"
            setOnClickListener { refreshAlerts() }
        }
        val drain = Button(this).apply {
            text = "Drain alert ack actions"
            setOnClickListener { drainAlertActions() }
        }
        layout.addView(title)
        layout.addView(summary)
        layout.addView(refresh)
        layout.addView(drain)
        setContentView(layout)
    }

    private fun refreshAlerts() {
        val settings = ApiSettingsStore(this)
        val session = SecureSessionStore(this).load()
        val familyId = session?.familyId ?: QuickRecordActivity.DEV_FAMILY_ID
        summary.text = "Refreshing alerts..."
        Thread {
            val result = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .getJson("/api/v1/alerts?family_id=$familyId")
            runOnUiThread { summary.text = "alerts=${result.statusCode}\n${result.body.take(400)}" }
        }.start()
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
            runOnUiThread { summary.text = "acked=${result.succeeded} failed=${result.failed}" }
        }.start()
    }
}
