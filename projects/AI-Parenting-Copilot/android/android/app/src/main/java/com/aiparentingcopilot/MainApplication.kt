// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:25:00

package com.aiparentingcopilot

import android.app.Application

class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        NotificationHelper.ensureChannels(this)
        BackgroundDrainScheduler.schedulePeriodic(this)
    }
}
