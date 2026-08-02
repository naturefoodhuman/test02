// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 16:14:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.os.Looper
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import java.time.Instant
import java.util.UUID
import org.json.JSONObject

/** Native Quick Record fallback that writes locally before any network sync. */
class QuickRecordActivity : Activity() {
    private lateinit var store: LocalEventStore
    private lateinit var status: TextView
    private lateinit var copilotText: EditText

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
        copilotText = EditText(this).apply {
            hint = "Voice text, e.g. 刚喂了90ml奶"
            minLines = 2
        }
        val save = Button(this).apply { text = "Save feeding locally" }
        val saveAndDrain = Button(this).apply { text = "Save and trigger drain" }
        val parseWithCopilot = Button(this).apply { text = "Parse text with Copilot and save locally" }
        status = TextView(this).apply {
            textSize = 16f
            gravity = Gravity.CENTER
        }
        save.setOnClickListener {
            val amountMl = amount.text.toString().toDoubleOrNull() ?: 0.0
            saveFeeding(amountMl, triggerDrain = false)
        }
        saveAndDrain.setOnClickListener {
            val amountMl = amount.text.toString().toDoubleOrNull() ?: 0.0
            saveFeeding(amountMl, triggerDrain = true)
        }
        parseWithCopilot.setOnClickListener {
            parseCopilotAndSave(copilotText.text.toString())
        }

        layout.addView(title)
        layout.addView(amount)
        layout.addView(save)
        layout.addView(saveAndDrain)
        layout.addView(copilotText)
        layout.addView(parseWithCopilot)
        layout.addView(status)
        setContentView(layout)
        refreshStatus()
    }

    private fun saveFeeding(amountMl: Double, triggerDrain: Boolean) {
        saveLocalEvent(
            eventType = "feeding",
            payloadJson = JSONObject().put("amount_ml", amountMl).toString(),
            confidence = 1.0,
            triggerDrain = triggerDrain,
        )
    }

    private fun parseCopilotAndSave(rawText: String) {
        val text = rawText.trim()
        if (text.isBlank()) {
            status.text = "Enter text before Copilot parse. Pending sync: ${store.pendingCount()}"
            return
        }
        val session = SecureSessionStore(this).load()
        val babyId = session?.babyId ?: intent.getStringExtra("baby_id") ?: DEV_BABY_ID
        val familyId = session?.familyId ?: intent.getStringExtra("family_id") ?: DEV_FAMILY_ID
        val payload = JSONObject()
            .put("text", text)
            .put("baby_id", babyId)
            .put("family_id", familyId)
            .put("intent", "record")
            .put("context", JSONObject())
        status.text = "Calling Copilot..."
        Thread {
            val message = try {
                val result = NativeApiClient(ApiSettingsStore(this).baseUrl(), session?.accessToken)
                    .postJsonResult("/api/v1/copilot/query", payload.toString())
                if (result.statusCode in 200..299) {
                    saveServerCandidate(text, result.body)
                } else {
                    saveFallbackCandidate(
                        text,
                        "Copilot unavailable (${result.statusCode}); saved local fallback",
                    )
                }
            } catch (exc: Exception) {
                saveFallbackCandidate(text, "Copilot error (${exc.message}); saved local fallback")
            }
            runOnUiThread { status.text = message }
        }.start()
    }

    private fun saveServerCandidate(text: String, responseBody: String): String {
        return try {
            val candidate = JSONObject(responseBody)
                .optJSONObject("copilot_response")
                ?.optJSONObject("payload")
                ?.optJSONObject("record_candidate")
            val eventType = candidate?.optString("event_type", "unknown") ?: "unknown"
            val normalizedPayload = candidate?.optJSONObject("normalized_payload")
                ?: JSONObject().put("raw_text", text)
            val confidence = candidate?.optDouble("confidence", 0.2) ?: 0.2
            saveLocalEvent(
                eventType = eventType,
                payloadJson = normalizedPayload.toString(),
                confidence = confidence,
                triggerDrain = false,
            )
            "Copilot candidate saved locally: $eventType, pending=${store.pendingCount()}"
        } catch (exc: Exception) {
            saveFallbackCandidate(text, "Copilot response parse failed (${exc.message}); saved local fallback")
        }
    }

    private fun saveFallbackCandidate(text: String, prefix: String): String {
        val feedingAmount = listOf(
            Regex("(?:喂|喝|奶).*?(\\d+(?:\\.\\d+)?)\\s*(?:ml|毫升)", RegexOption.IGNORE_CASE),
            Regex("(\\d+(?:\\.\\d+)?)\\s*(?:ml|毫升).*?(?:奶)", RegexOption.IGNORE_CASE),
        ).firstNotNullOfOrNull { pattern -> pattern.find(text)?.groupValues?.get(1)?.toDoubleOrNull() }
        val tempValue = Regex("(\\d{1,3}(?:\\.\\d+)?)\\s*(?:度|℃|c)", RegexOption.IGNORE_CASE)
            .find(text)
            ?.groupValues
            ?.get(1)
            ?.toDoubleOrNull()
        val eventType: String
        val payload = JSONObject()
        val confidence: Double
        when {
            feedingAmount != null -> {
                eventType = "feeding"
                payload.put("amount_ml", feedingAmount)
                confidence = 0.88
            }
            tempValue != null -> {
                eventType = "temperature"
                payload.put("value_c", tempValue)
                confidence = 0.85
            }
            Regex("尿布|纸尿裤|便便|大便|尿").containsMatchIn(text) -> {
                eventType = "diaper"
                payload.put("note", text).put("diaper_type", "unknown")
                confidence = 0.75
            }
            Regex("睡|醒|入睡").containsMatchIn(text) -> {
                eventType = "sleep"
                payload.put("note", text)
                confidence = 0.70
            }
            else -> {
                eventType = "unknown"
                payload.put("raw_text", text)
                confidence = 0.20
            }
        }
        saveLocalEvent(
            eventType = eventType,
            payloadJson = payload.toString(),
            confidence = confidence,
            triggerDrain = false,
        )
        return "$prefix: $eventType, pending=${store.pendingCount()}"
    }

    private fun saveLocalEvent(
        eventType: String,
        payloadJson: String,
        confidence: Double,
        triggerDrain: Boolean,
    ) {
        val now = Instant.now().toString()
        val session = SecureSessionStore(this).load()
        val event = LocalObservationEvent(
            eventId = UUID.randomUUID().toString(),
            babyId = session?.babyId ?: intent.getStringExtra("baby_id") ?: DEV_BABY_ID,
            familyId = session?.familyId ?: intent.getStringExtra("family_id") ?: DEV_FAMILY_ID,
            userId = session?.userId ?: intent.getStringExtra("user_id"),
            deviceId = session?.deviceId ?: intent.getStringExtra("device_id"),
            eventType = eventType,
            startTime = now,
            clientCreatedAt = now,
            payloadJson = payloadJson,
            source = "manual",
            confidence = confidence,
        )
        store.insertPending(event)
        if (triggerDrain) {
            BackgroundDrainScheduler.triggerNow(this)
        }
        refreshStatus()
    }

    private fun refreshStatus() {
        val message = "Pending sync: ${store.pendingCount()}"
        if (Looper.myLooper() == Looper.getMainLooper()) {
            status.text = message
        } else {
            runOnUiThread { status.text = message }
        }
    }

    companion object {
        const val DEV_FAMILY_ID = "dev-family"
        const val DEV_BABY_ID = "dev-baby"
    }
}
