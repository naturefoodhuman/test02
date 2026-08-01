// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 17:26:00

package com.aiparentingcopilot

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "AI Parenting Copilot Android shell"
            textSize = 22f
            gravity = Gravity.CENTER
        }
        layout.addView(title)
        addButton(layout, "Today", TodayActivity::class.java)
        addButton(layout, "Quick Record", QuickRecordActivity::class.java)
        addButton(layout, "Timeline", TimelineActivity::class.java)
        addButton(layout, "Alert Center", AlertCenterActivity::class.java)
        addButton(layout, "Sleep Session", SleepSessionActivity::class.java)
        addButton(layout, "Pending Sync", PendingEventsActivity::class.java)
        addButton(layout, "API Settings / Drain", ApiSettingsActivity::class.java)
        val alertDemo = Button(this).apply {
            text = "Critical Alert Demo"
            setOnClickListener {
                val intent = Intent(this@MainActivity, CriticalAlertActivity::class.java).apply {
                    putExtra("alert_id", "demo-alert")
                    putExtra("level", "red")
                    putExtra("type", "demo")
                }
                startActivity(intent)
            }
        }
        layout.addView(alertDemo)
        setContentView(layout)
    }

    private fun addButton(layout: LinearLayout, label: String, target: Class<out Activity>) {
        layout.addView(
            Button(this).apply {
                text = label
                setOnClickListener { startActivity(Intent(this@MainActivity, target)) }
            },
        )
    }
}
