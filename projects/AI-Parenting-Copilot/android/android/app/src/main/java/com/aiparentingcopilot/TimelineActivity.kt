// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 19:27:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Native Timeline fallback listing local pending events and optional server events. */
class TimelineActivity : Activity() {
    private lateinit var body: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val events = LocalEventStore(this).pending()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Timeline"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        body = TextView(this).apply {
            text = events.joinToString(separator = "\n") { event ->
                "${event.eventType} · ${event.source} · pending=${event.pendingSync}"
            }.ifBlank { "No local events" }
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val refresh = Button(this).apply {
            text = "Refresh server timeline"
            setOnClickListener { refreshServerEvents() }
        }
        layout.addView(title)
        layout.addView(body)
        layout.addView(refresh)
        setContentView(layout)
    }

    private fun refreshServerEvents() {
        val settings = ApiSettingsStore(this)
        val session = SecureSessionStore(this).load()
        val babyId = session?.babyId ?: QuickRecordActivity.DEV_BABY_ID
        body.text = "Refreshing server events..."
        Thread {
            val result = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .getJson("/api/v1/events?baby_id=$babyId")
            runOnUiThread { body.text = "events=${result.statusCode}\n${result.body.take(400)}" }
        }.start()
    }
}
