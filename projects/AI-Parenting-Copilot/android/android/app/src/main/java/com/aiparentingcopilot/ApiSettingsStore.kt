// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:20:00

package com.aiparentingcopilot

import android.content.Context

/** Local native settings for fallback API/drain flows. */
class ApiSettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun baseUrl(): String = prefs.getString("api_base_url", DEFAULT_EMULATOR_API) ?: DEFAULT_EMULATOR_API

    fun setBaseUrl(baseUrl: String) {
        prefs.edit().putString("api_base_url", baseUrl.trimEnd('/')).apply()
    }

    fun saveLastDrain(pending: NativeDrainResult, alertAck: NativeDrainResult) {
        prefs.edit()
            .putString(
                "last_drain_summary",
                "pending=${pending.succeeded}/${pending.attempted}, ack=${alertAck.succeeded}/${alertAck.attempted}, failed=${pending.failed + alertAck.failed}",
            )
            .apply()
    }

    fun lastDrainSummary(): String = prefs.getString("last_drain_summary", "No drain yet") ?: "No drain yet"

    companion object {
        private const val PREFS = "parenting_api_settings"
        const val DEFAULT_EMULATOR_API = "http://10.0.2.2:8000"
    }
}
