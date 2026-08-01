// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 02:58:00

package com.aiparentingcopilot

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build

/** Native notification primitives for full-screen alert fallback. */
object NotificationHelper {
    const val CRITICAL_CHANNEL_ID = "parenting-critical-alerts"
    const val DEFAULT_CHANNEL_ID = "parenting-alerts"

    fun ensureChannels(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(NotificationManager::class.java)
        val critical = NotificationChannel(
            CRITICAL_CHANNEL_ID,
            "Parenting Critical Alerts",
            NotificationManager.IMPORTANCE_HIGH,
        )
        critical.description = "Red/orange parenting alerts requiring immediate attention"
        val regular = NotificationChannel(
            DEFAULT_CHANNEL_ID,
            "Parenting Alerts",
            NotificationManager.IMPORTANCE_DEFAULT,
        )
        manager.createNotificationChannel(critical)
        manager.createNotificationChannel(regular)
    }

    fun fullScreenIntent(context: Context, payload: AlertPayload): PendingIntent {
        val intent = Intent(context, CriticalAlertActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("alert_id", payload.alertId)
            putExtra("level", payload.level)
            putExtra("type", payload.type)
        }
        return PendingIntent.getActivity(
            context,
            payload.alertId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }
}
