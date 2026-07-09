-- 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
-- 创建时间（北京时间）：2026-07-08 23:35:00


SELECT 'CREATE DATABASE powersync_storage'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'powersync_storage')\gexec
