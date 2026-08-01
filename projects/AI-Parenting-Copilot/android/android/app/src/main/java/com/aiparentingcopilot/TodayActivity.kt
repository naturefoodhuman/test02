// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 17:20:00

package com.aiparentingcopilot

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Native Today fallback showing local-first operational state. */
class TodayActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val store = LocalEventStore(this)
        val settings = ApiSettingsStore(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Today"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        val pending = TextView(this).apply {
            text = "Pending sync: ${store.pendingCount()}"
            textSize = 18f
            gravity = Gravity.CENTER
        }
        val lastDrain = TextView(this).apply {
            text = settings.lastDrainSummary()
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val quickRecord = Button(this).apply {
            text = "Quick Record"
            setOnClickListener { startActivity(Intent(this@TodayActivity, QuickRecordActivity::class.java)) }
        }
        val pendingEvents = Button(this).apply {
            text = "Pending Sync"
            setOnClickListener { startActivity(Intent(this@TodayActivity, PendingEventsActivity::class.java)) }
        }
        layout.addView(title)
        layout.addView(pending)
        layout.addView(lastDrain)
        layout.addView(quickRecord)
        layout.addView(pendingEvents)
        setContentView(layout)
    }
}
