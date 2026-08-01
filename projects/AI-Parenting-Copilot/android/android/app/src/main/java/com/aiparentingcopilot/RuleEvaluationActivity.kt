// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 22:48:00

package com.aiparentingcopilot

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject

/** Native Rule Engine evaluation fallback screen.
 *
 * Calls server Rule Engine endpoints directly. It does not ask LLMs to produce
 * medication dose, triage threshold, vaccine, or growth decisions.
 */
class RuleEvaluationActivity : Activity() {
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }
        val title = TextView(this).apply {
            text = "Rule Engine"
            textSize = 24f
            gravity = Gravity.CENTER
        }
        status = TextView(this).apply {
            text = "Rule Engine only. No LLM dose/triage generation."
            textSize = 16f
            gravity = Gravity.CENTER
        }
        layout.addView(title)
        layout.addView(status)
        layout.addView(button("Medication safety") { evaluateMedication() })
        layout.addView(button("Triage fever") { evaluateTriage() })
        layout.addView(button("Vaccine plan") { evaluateVaccine() })
        layout.addView(button("Growth check") { evaluateGrowth() })
        setContentView(layout)
    }

    private fun button(label: String, action: () -> Unit): Button {
        return Button(this).apply {
            text = label
            setOnClickListener { action() }
        }
    }

    private fun evaluateMedication() {
        val payload = JSONObject()
            .put("medication_key", "acetaminophen")
            .put("baby_age_months", 4)
            .put("weight_kg", 6.0)
            .put("concentration_mg_per_ml", 32.0)
        evaluate("medication", payload)
    }

    private fun evaluateTriage() {
        val payload = JSONObject()
            .put("baby_age_months", 2)
            .put("temperature_c", 38.2)
        evaluate("triage", payload)
    }

    private fun evaluateVaccine() {
        val payload = JSONObject()
            .put("birth_date", "2026-07-09")
            .put("as_of", "2026-07-09")
        evaluate("vaccine", payload)
    }

    private fun evaluateGrowth() {
        val payload = JSONObject()
            .put("sex", "male")
            .put("age_months", 3)
            .put("metric", "weight_kg")
            .put("value", 6.4)
        evaluate("growth", payload)
    }

    private fun evaluate(domain: String, payload: JSONObject) {
        status.text = "Evaluating $domain..."
        Thread {
            val settings = ApiSettingsStore(this)
            val session = SecureSessionStore(this).load()
            val body = JSONObject().put("payload", payload).toString()
            val result = NativeApiClient(settings.baseUrl(), session?.accessToken)
                .postJsonResult("/api/v1/rules/evaluate/$domain", body)
            runOnUiThread {
                status.text = "$domain=${result.statusCode}\n${result.body.take(360)}"
            }
        }.start()
    }
}
