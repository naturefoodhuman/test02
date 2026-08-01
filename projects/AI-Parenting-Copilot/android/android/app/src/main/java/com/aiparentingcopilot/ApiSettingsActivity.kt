// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:24:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/** Native settings screen for local API base URL and drain diagnostics. */
class ApiSettingsActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val settings = ApiSettingsStore(this)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "API Settings"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        val baseUrl = EditText(this).apply {
            hint = ApiSettingsStore.DEFAULT_EMULATOR_API
            setText(settings.baseUrl())
        }
        val summary = TextView(this).apply {
            text = settings.lastDrainSummary()
            textSize = 16f
            gravity = Gravity.CENTER
        }
        val save = Button(this).apply {
            text = "Save API URL"
            setOnClickListener {
                settings.setBaseUrl(baseUrl.text.toString())
                summary.text = "Saved ${settings.baseUrl()}"
            }
        }
        val trigger = Button(this).apply {
            text = "Trigger drain now"
            setOnClickListener {
                BackgroundDrainScheduler.triggerNow(this@ApiSettingsActivity)
                summary.text = "Drain scheduled"
            }
        }
        layout.addView(title)
        layout.addView(baseUrl)
        layout.addView(save)
        layout.addView(trigger)
        layout.addView(summary)
        setContentView(layout)
    }
}
