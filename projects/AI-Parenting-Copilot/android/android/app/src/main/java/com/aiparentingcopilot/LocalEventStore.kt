// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-08-01 04:36:00

package com.aiparentingcopilot

import android.content.ContentValues
import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/** Native SQLite pending event store for offline-first Quick Record.
 *
 * PowerSync remains the sync engine. This store is a small native fallback for
 * local writes and pending-sync visibility before the RN/op-sqlite bridge is
 * connected on device.
 */
class LocalEventStore(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS observation_event_local (
                event_id TEXT PRIMARY KEY,
                baby_id TEXT NOT NULL,
                family_id TEXT NOT NULL,
                user_id TEXT,
                device_id TEXT,
                event_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                client_created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                correction_of TEXT,
                is_deleted INTEGER NOT NULL DEFAULT 0,
                pending_sync INTEGER NOT NULL DEFAULT 1
            )
            """.trimIndent(),
        )
        db.execSQL(
            "CREATE INDEX IF NOT EXISTS ix_observation_event_local_pending ON observation_event_local(pending_sync)",
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        if (oldVersion < newVersion) {
            onCreate(db)
        }
    }

    fun insertPending(event: LocalObservationEvent): LocalObservationEvent {
        writableDatabase.insertWithOnConflict(
            TABLE,
            null,
            event.toContentValues(pendingSync = true),
            SQLiteDatabase.CONFLICT_REPLACE,
        )
        return event.copy(pendingSync = true)
    }

    fun markSynced(eventId: String) {
        val values = ContentValues().apply { put("pending_sync", 0) }
        writableDatabase.update(TABLE, values, "event_id = ?", arrayOf(eventId))
    }

    fun pending(): List<LocalObservationEvent> {
        readableDatabase.query(
            TABLE,
            null,
            "pending_sync = 1",
            emptyArray<String>(),
            null,
            null,
            "client_created_at ASC",
        ).use { cursor -> return cursor.readEvents() }
    }

    fun pendingCount(): Int = pending().size

    private fun LocalObservationEvent.toContentValues(pendingSync: Boolean): ContentValues {
        return ContentValues().apply {
            put("event_id", eventId)
            put("baby_id", babyId)
            put("family_id", familyId)
            put("user_id", userId)
            put("device_id", deviceId)
            put("event_type", eventType)
            put("start_time", startTime)
            put("client_created_at", clientCreatedAt)
            put("payload_json", payloadJson)
            put("source", source)
            put("confidence", confidence)
            put("correction_of", correctionOf)
            put("is_deleted", if (isDeleted) 1 else 0)
            put("pending_sync", if (pendingSync) 1 else 0)
        }
    }

    private fun Cursor.readEvents(): List<LocalObservationEvent> {
        val rows = mutableListOf<LocalObservationEvent>()
        while (moveToNext()) {
            rows.add(
                LocalObservationEvent(
                    eventId = getString(getColumnIndexOrThrow("event_id")),
                    babyId = getString(getColumnIndexOrThrow("baby_id")),
                    familyId = getString(getColumnIndexOrThrow("family_id")),
                    userId = getStringOrNull("user_id"),
                    deviceId = getStringOrNull("device_id"),
                    eventType = getString(getColumnIndexOrThrow("event_type")),
                    startTime = getString(getColumnIndexOrThrow("start_time")),
                    clientCreatedAt = getString(getColumnIndexOrThrow("client_created_at")),
                    payloadJson = getString(getColumnIndexOrThrow("payload_json")),
                    source = getString(getColumnIndexOrThrow("source")),
                    confidence = getDouble(getColumnIndexOrThrow("confidence")),
                    correctionOf = getStringOrNull("correction_of"),
                    isDeleted = getInt(getColumnIndexOrThrow("is_deleted")) == 1,
                    pendingSync = getInt(getColumnIndexOrThrow("pending_sync")) == 1,
                ),
            )
        }
        return rows
    }

    private fun Cursor.getStringOrNull(column: String): String? {
        val index = getColumnIndexOrThrow(column)
        return if (isNull(index)) null else getString(index)
    }

    companion object {
        private const val DB_NAME = "ai_parenting_copilot_local.db"
        private const val DB_VERSION = 1
        private const val TABLE = "observation_event_local"
    }
}
