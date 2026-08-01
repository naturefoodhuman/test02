// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:00:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Simple native pending-sync status screen for offline-write verification. */
class PendingEventsActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val store = LocalEventStore(this)
        val pending = store.pending()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Pending sync events: ${pending.size}"
            textSize = 22f
            gravity = Gravity.CENTER
        }
        val detail = TextView(this).apply {
            text = pending.take(5).joinToString(separator = "\n") { event ->
                "${event.eventType} ${event.clientCreatedAt}"
            }.ifBlank { "No pending events" }
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val drain = Button(this).apply {
            text = "Drain pending to server"
            setOnClickListener {
                text = "Draining..."
                Thread {
                    val baseUrl = intent.getStringExtra("api_base_url") ?: DEFAULT_EMULATOR_API
                    val result = PendingSyncDrainer(
                        this@PendingEventsActivity,
                        NativeApiClient(baseUrl),
                    ).drain()
                    runOnUiThread {
                        text = "Drain pending to server"
                        detail.text = "synced=${result.succeeded} failed=${result.failed}"
                    }
                }.start()
            }
        }
        layout.addView(title)
        layout.addView(detail)
        layout.addView(drain)
        setContentView(layout)
    }

    companion object {
        const val DEFAULT_EMULATOR_API = "http://10.0.2.2:8000"
    }
}
