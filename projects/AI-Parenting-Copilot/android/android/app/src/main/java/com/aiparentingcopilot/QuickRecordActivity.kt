// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 09:35:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import java.time.Instant
import java.util.UUID

/** Native Quick Record fallback that writes locally before any network sync. */
class QuickRecordActivity : Activity() {
    private lateinit var store: LocalEventStore
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = LocalEventStore(this)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Quick Record"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        val amount = EditText(this).apply {
            hint = "Milk amount ml"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
        }
        val save = Button(this).apply { text = "Save feeding locally" }
        status = TextView(this).apply {
            textSize = 16f
            gravity = Gravity.CENTER
        }
        save.setOnClickListener {
            val amountMl = amount.text.toString().toDoubleOrNull() ?: 0.0
            saveFeeding(amountMl)
        }

        layout.addView(title)
        layout.addView(amount)
        layout.addView(save)
        layout.addView(status)
        setContentView(layout)
        refreshStatus()
    }

    private fun saveFeeding(amountMl: Double) {
        val now = Instant.now().toString()
        val event = LocalObservationEvent(
            eventId = UUID.randomUUID().toString(),
            babyId = intent.getStringExtra("baby_id") ?: DEV_BABY_ID,
            familyId = intent.getStringExtra("family_id") ?: DEV_FAMILY_ID,
            userId = intent.getStringExtra("user_id"),
            deviceId = intent.getStringExtra("device_id"),
            eventType = "feeding",
            startTime = now,
            clientCreatedAt = now,
            payloadJson = "{\"amount_ml\":$amountMl}",
            source = "manual",
            confidence = 1.0,
        )
        store.insertPending(event)
        refreshStatus()
    }

    private fun refreshStatus() {
        status.text = "Pending sync: ${store.pendingCount()}"
    }

    companion object {
        const val DEV_FAMILY_ID = "dev-family"
        const val DEV_BABY_ID = "dev-baby"
    }
}
