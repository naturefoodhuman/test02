// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 15:58:00

package com.aiparentingcopilot

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Records local alert actions so sync/API ack can drain them later. */
class AlertActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val payload = AlertPayload.fromIntent(intent)
        val action = intent.getStringExtra("action") ?: "unknown"
        recordLocalAction(context, payload.alertId, action)
    }

    companion object {
        const val ACTION_ALERT_LOCAL = "com.aiparentingcopilot.ALERT_LOCAL_ACTION"
        private const val PREFS = "parenting_alert_actions"

        fun recordLocalAction(context: Context, alertId: String, action: String) {
            if (alertId.isBlank()) return
            val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            prefs.edit()
                .putString(alertId, action)
                .apply()
        }

        fun drainLocalActions(context: Context): List<LocalAlertAction> {
            val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val actions = prefs.all.mapNotNull { (alertId, action) ->
                val actionText = action as? String ?: return@mapNotNull null
                LocalAlertAction(alertId = alertId, action = actionText)
            }
            prefs.edit().clear().apply()
            return actions
        }
    }
}

data class LocalAlertAction(val alertId: String, val action: String)
