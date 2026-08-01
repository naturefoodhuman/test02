// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 19:25:00

package com.aiparentingcopilot

import java.net.HttpURLConnection
import java.net.URL

/** Minimal native API client used by fallback screens before RN bridge is wired. */
class NativeApiClient(
    private val baseUrl: String,
    private val accessToken: String? = null,
) {
    fun getJson(path: String): NativeHttpResult {
        val connection = open(path, "GET")
        return readResult(connection)
    }

    fun postJson(path: String, json: String): Int {
        return postJsonResult(path, json).statusCode
    }

    fun postJsonResult(path: String, json: String): NativeHttpResult {
        val connection = open(path, "POST").apply { doOutput = true }
        connection.outputStream.use { output -> output.write(json.toByteArray(Charsets.UTF_8)) }
        return readResult(connection)
    }

    private fun open(path: String, method: String): HttpURLConnection {
        val url = URL(baseUrl.trimEnd('/') + path)
        return (url.openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 5_000
            readTimeout = 5_000
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Accept", "application/json")
            if (!accessToken.isNullOrBlank()) {
                setRequestProperty("Authorization", "Bearer $accessToken")
            }
        }
    }

    private fun readResult(connection: HttpURLConnection): NativeHttpResult {
        return try {
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            NativeHttpResult(statusCode = code, body = body)
        } finally {
            connection.disconnect()
        }
    }
}

data class NativeHttpResult(val statusCode: Int, val body: String)

data class NativeDrainResult(
    val attempted: Int,
    val succeeded: Int,
    val failed: Int,
)
