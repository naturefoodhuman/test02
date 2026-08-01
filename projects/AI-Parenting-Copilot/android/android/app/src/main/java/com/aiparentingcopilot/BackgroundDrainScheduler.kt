// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 16:21:00

package com.aiparentingcopilot

import android.app.job.JobInfo
import android.app.job.JobScheduler
import android.content.ComponentName
import android.content.Context

/** Schedules network-required drains for pending local records and alert acks. */
object BackgroundDrainScheduler {
    private const val PERIODIC_JOB_ID = 41001
    private const val IMMEDIATE_JOB_ID = 41002
    private const val PERIODIC_INTERVAL_MS = 15 * 60 * 1000L

    fun schedulePeriodic(context: Context) {
        val scheduler = context.getSystemService(JobScheduler::class.java)
        scheduler.schedule(baseJob(context, PERIODIC_JOB_ID).setPeriodic(PERIODIC_INTERVAL_MS).build())
    }

    fun triggerNow(context: Context) {
        val scheduler = context.getSystemService(JobScheduler::class.java)
        scheduler.schedule(baseJob(context, IMMEDIATE_JOB_ID).setOverrideDeadline(0).build())
    }

    private fun baseJob(context: Context, jobId: Int): JobInfo.Builder {
        return JobInfo.Builder(jobId, ComponentName(context, BackgroundDrainJobService::class.java))
            .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
            .setPersisted(true)
            .setRequiresCharging(false)
    }
}
