// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 17:21:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

/** Native Timeline fallback listing local pending events. */
class TimelineActivity : Activity() {
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
        val body = TextView(this).apply {
            text = events.joinToString(separator = "\n") { event ->
                "${event.eventType} · ${event.source} · pending=${event.pendingSync}"
            }.ifBlank { "No local events" }
            textSize = 16f
            gravity = Gravity.CENTER
        }
        layout.addView(title)
        layout.addView(body)
        setContentView(layout)
    }
}
