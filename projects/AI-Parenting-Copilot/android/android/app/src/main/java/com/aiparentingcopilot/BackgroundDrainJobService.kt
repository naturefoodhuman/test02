// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:22:00

package com.aiparentingcopilot

import android.app.job.JobParameters
import android.app.job.JobService

/** JobScheduler service that drains pending local events and local alert ack actions. */
class BackgroundDrainJobService : JobService() {
    override fun onStartJob(params: JobParameters?): Boolean {
        Thread {
            val settings = ApiSettingsStore(this)
            val session = SecureSessionStore(this).load()
            val api = NativeApiClient(settings.baseUrl(), session?.accessToken)
            val pending = PendingSyncDrainer(this, api).drain()
            val alertAck = if (session != null) {
                AlertAckDrainer(this, api, ackBy = session.userId, deviceId = session.deviceId).drain()
            } else {
                NativeDrainResult(attempted = 0, succeeded = 0, failed = 0)
            }
            settings.saveLastDrain(pending, alertAck)
            jobFinished(params, pending.failed > 0 || alertAck.failed > 0)
        }.start()
        return true
    }

    override fun onStopJob(params: JobParameters?): Boolean {
        return true
    }
}
