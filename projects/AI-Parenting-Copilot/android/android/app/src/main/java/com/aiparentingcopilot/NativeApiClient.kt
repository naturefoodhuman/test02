// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 15:55:00

package com.aiparentingcopilot

import java.net.HttpURLConnection
import java.net.URL

/** Minimal native API client used by fallback screens before RN bridge is wired. */
class NativeApiClient(
    private val baseUrl: String,
    private val accessToken: String? = null,
) {
    fun postJson(path: String, json: String): Int {
        val url = URL(baseUrl.trimEnd('/') + path)
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 5_000
            readTimeout = 5_000
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Accept", "application/json")
            if (!accessToken.isNullOrBlank()) {
                setRequestProperty("Authorization", "Bearer $accessToken")
            }
        }
        return try {
            connection.outputStream.use { output ->
                output.write(json.toByteArray(Charsets.UTF_8))
            }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            stream?.close()
            code
        } finally {
            connection.disconnect()
        }
    }
}

data class NativeDrainResult(
    val attempted: Int,
    val succeeded: Int,
    val failed: Int,
)
