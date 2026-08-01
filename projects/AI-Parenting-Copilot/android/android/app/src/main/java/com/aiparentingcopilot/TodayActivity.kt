// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 19:26:00

package com.aiparentingcopilot

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/** Native Today fallback showing local-first and server operational state. */
class TodayActivity : Activity() {
    private lateinit var status: TextView

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
        status = TextView(this).apply {
            text = "Pending sync: ${store.pendingCount()}\n${settings.lastDrainSummary()}"
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val refreshHealth = Button(this).apply {
            text = "Refresh server health"
            setOnClickListener { refreshHealth(settings.baseUrl()) }
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
        layout.addView(status)
        layout.addView(refreshHealth)
        layout.addView(quickRecord)
        layout.addView(pendingEvents)
        setContentView(layout)
    }

    private fun refreshHealth(baseUrl: String) {
        status.text = "Refreshing health..."
        Thread {
            val result = NativeApiClient(baseUrl).getJson("/api/v1/system/health")
            runOnUiThread {
                status.text = "health=${result.statusCode}\n${result.body.take(240)}"
            }
        }.start()
    }
}
