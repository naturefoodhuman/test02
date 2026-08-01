// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 02:55:00

package com.aiparentingcopilot

import android.content.Intent

/** Trigger-only alert payload mirrored from server FCM delivery. */
data class AlertPayload(
    val alertId: String,
    val level: String,
    val type: String,
) {
    companion object {
        fun fromIntent(intent: Intent): AlertPayload {
            return AlertPayload(
                alertId = intent.getStringExtra("alert_id") ?: "",
                level = intent.getStringExtra("level") ?: "unknown",
                type = intent.getStringExtra("type") ?: "unknown",
            )
        }
    }

    fun extras(): Map<String, String> = mapOf(
        "alert_id" to alertId,
        "level" to level,
        "type" to type,
    )
}
