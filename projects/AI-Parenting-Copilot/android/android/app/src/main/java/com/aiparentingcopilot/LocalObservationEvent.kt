// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 04:35:00

package com.aiparentingcopilot

/** Local-first ObservationEvent row mirrored from the server sync contract. */
data class LocalObservationEvent(
    val eventId: String,
    val babyId: String,
    val familyId: String,
    val userId: String?,
    val deviceId: String?,
    val eventType: String,
    val startTime: String,
    val clientCreatedAt: String,
    val payloadJson: String,
    val source: String,
    val confidence: Double,
    val correctionOf: String? = null,
    val isDeleted: Boolean = false,
    val pendingSync: Boolean = true,
)
