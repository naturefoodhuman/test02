// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-02 16:46:00

package com.aiparentingcopilot

import android.content.Context
import org.json.JSONObject

/** Drains locally recorded alert ack actions to the server Alert API. */
class AlertAckDrainer(
    context: Context,
    private val apiClient: NativeApiClient,
    private val ackBy: String,
    private val deviceId: String? = null,
) {
    private val appContext = context.applicationContext

    fun drain(): NativeDrainResult {
        val actions = AlertActionReceiver.drainLocalActions(appContext)
        var succeeded = 0
        var failed = 0
        var attempted = 0
        for (action in actions) {
            if (action.action != "ack") continue
            attempted += 1
            val body = JSONObject()
                .put("ack_by", ackBy)
                .put("device_id", deviceId)
                .toString()
            val statusCode = try {
                apiClient.postJson("/api/v1/alerts/${action.alertId}/ack", body)
            } catch (_: Exception) {
                null
            }
            if (statusCode != null && statusCode in 200..299) {
                succeeded += 1
            } else {
                failed += 1
                AlertActionReceiver.recordLocalAction(appContext, action.alertId, action.action)
            }
        }
        return NativeDrainResult(attempted = attempted, succeeded = succeeded, failed = failed)
    }
}
