// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:23:00

package com.aiparentingcopilot

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Restores background drains after device reboot. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            BackgroundDrainScheduler.schedulePeriodic(context)
        }
    }
}
