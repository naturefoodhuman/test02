// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 15:56:00

package com.aiparentingcopilot

import android.content.Context
import org.json.JSONObject

/** Drains native pending ObservationEvents to the server Events API. */
class PendingSyncDrainer(
    context: Context,
    private val apiClient: NativeApiClient,
) {
    private val store = LocalEventStore(context)

    fun drain(): NativeDrainResult {
        val pending = store.pending()
        var succeeded = 0
        var failed = 0
        for (event in pending) {
            val statusCode = apiClient.postJson("/api/v1/events", event.toServerJson().toString())
            if (statusCode in 200..299) {
                store.markSynced(event.eventId)
                succeeded += 1
            } else {
                failed += 1
            }
        }
        return NativeDrainResult(attempted = pending.size, succeeded = succeeded, failed = failed)
    }

    private fun LocalObservationEvent.toServerJson(): JSONObject {
        return JSONObject()
            .put("event_id", eventId)
            .put("baby_id", babyId)
            .put("family_id", familyId)
            .put("user_id", userId)
            .put("device_id", deviceId)
            .put("event_type", eventType)
            .put("start_time", startTime)
            .put("client_created_at", clientCreatedAt)
            .put("payload", JSONObject(payloadJson))
            .put("source", source)
            .put("confidence", confidence)
            .put("correction_of", correctionOf)
            .put("is_deleted", isDeleted)
    }
}
