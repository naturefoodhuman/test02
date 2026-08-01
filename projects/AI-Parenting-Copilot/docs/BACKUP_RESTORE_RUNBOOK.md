<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 13:10:00
-->

# BACKUP_RESTORE_RUNBOOK —— PostgreSQL / Media 备份与恢复演练

## 1. 备份 dry-run

```bash
cd projects/AI-Parenting-Copilot
make backup-dry-run
```

输出包含：

- `pg_dump --format=custom --file ... <database_url>`
- media archive output path

## 2. 恢复 dry-run

```bash
make restore-dry-run
```

输出示例：

```text
pg_restore --dbname postgresql://parenting:parenting@127.0.0.1:5432/parenting_restore --clean runtime/backups/pg/latest.dump
```

## 3. 真实备份建议流程

```bash
export PARENTING_DATABASE__URL="postgresql://parenting:parenting@127.0.0.1:5432/parenting"
mkdir -p runtime/backups/pg runtime/backups/media
pg_dump --format=custom --file runtime/backups/pg/parenting-$(date -u +%Y%m%dT%H%M%SZ).dump "$PARENTING_DATABASE__URL"
tar -czf runtime/backups/media/media-$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C runtime/media files thumbs
```

## 4. 真实恢复演练建议流程

只恢复到 disposable database，不要覆盖生产库：

```bash
createdb parenting_restore || true
pg_restore --dbname postgresql://parenting:parenting@127.0.0.1:5432/parenting_restore --clean runtime/backups/pg/latest.dump
mkdir -p runtime/restore-drills/media
tar -xzf runtime/backups/media/latest.tar.gz -C runtime/restore-drills/media
```

恢复后检查：

```bash
PARENTING_DATABASE__URL="postgresql+asyncpg://parenting:parenting@127.0.0.1:5432/parenting_restore" make db-current
```

## 5. 验收标准

- `pg_restore --list` 可读取 dump。
- disposable restore DB 能运行 `db-current`。
- media archive 解压后只包含 encrypted media files / thumbnails。
- 恢复演练记录写入项目运维日志或外部家庭运维笔记。
