// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 02:56:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Full-screen local fallback UI for red/orange alerts.
 *
 * The activity displays only trigger metadata. It intentionally does not render
 * evidence, raw input, or medical recommendations delivered over FCM.
 */
class CriticalAlertActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val payload = AlertPayload.fromIntent(intent)
        setShowWhenLocked(true)
        setTurnScreenOn(true)

        val layout = LinearLayout(this)
        layout.orientation = LinearLayout.VERTICAL
        layout.gravity = Gravity.CENTER
        layout.setPadding(48, 48, 48, 48)

        val title = TextView(this)
        title.text = "AI Parenting Copilot Alert"
        title.textSize = 24f
        title.gravity = Gravity.CENTER

        val body = TextView(this)
        body.text = "${payload.level.uppercase()} alert: ${payload.type}\nOpen the app for evidence and action details."
        body.textSize = 18f
        body.gravity = Gravity.CENTER

        val ack = Button(this)
        ack.text = "Acknowledge"
        ack.setOnClickListener {
            AlertActionReceiver.recordLocalAction(this, payload.alertId, "ack")
            finish()
        }

        val dismiss = Button(this)
        dismiss.text = "Dismiss local screen"
        dismiss.setOnClickListener {
            AlertActionReceiver.recordLocalAction(this, payload.alertId, "dismiss_local")
            finish()
        }

        layout.addView(title)
        layout.addView(body)
        layout.addView(ack)
        layout.addView(dismiss)
        setContentView(layout)
    }
}
