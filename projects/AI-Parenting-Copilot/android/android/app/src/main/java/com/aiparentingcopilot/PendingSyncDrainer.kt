// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 16:35:00

package com.aiparentingcopilot

import android.content.Context
import org.json.JSONObject

/** Drains native pending ObservationEvents to the server Events API. */
class PendingSyncDrainer(
    private val context: Context,
    private val apiClient: NativeApiClient,
) {
    private val store = LocalEventStore(context)

    fun drain(): NativeDrainResult {
        val pending = store.pending()
        var succeeded = 0
        var failed = 0
        for (event in pending) {
            val statusCode = try {
                apiClient.postJson("/api/v1/events", event.toServerJson().toString())
            } catch (_: Exception) {
                failed += 1
                continue
            }
            if (statusCode in 200..299) {
                store.markSynced(event.eventId)
                succeeded += 1
            } else {
                failed += 1
            }
        }
        reportHeartbeat(pendingCount = store.pendingCount())
        return NativeDrainResult(attempted = pending.size, succeeded = succeeded, failed = failed)
    }

    private fun reportHeartbeat(pendingCount: Int) {
        val session = SecureSessionStore(context).load() ?: return
        val deviceId = session.deviceId ?: return
        val payload = JSONObject()
            .put("client_id", deviceId)
            .put("family_id", session.familyId)
            .put("pending_count", pendingCount)
        try {
            apiClient.postJson("/api/v1/sync/heartbeat", payload.toString())
        } catch (_: Exception) {
            // Heartbeat is best-effort; never drop or mark local events based on heartbeat failure.
        }
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
