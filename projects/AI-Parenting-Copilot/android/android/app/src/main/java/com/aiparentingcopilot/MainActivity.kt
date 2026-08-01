// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 09:37:00

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
        val quickRecord = Button(this).apply {
            text = "Quick Record"
            setOnClickListener { startActivity(Intent(this@MainActivity, QuickRecordActivity::class.java)) }
        }
        val pending = Button(this).apply {
            text = "Pending Sync"
            setOnClickListener { startActivity(Intent(this@MainActivity, PendingEventsActivity::class.java)) }
        }
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
        layout.addView(title)
        layout.addView(quickRecord)
        layout.addView(pending)
        layout.addView(alertDemo)
        setContentView(layout)
    }
}
