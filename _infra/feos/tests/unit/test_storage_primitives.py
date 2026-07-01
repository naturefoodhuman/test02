# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

from __future__ import annotations

import json

from _infra.feos.storage import BlobStore, FileLock, atomic_write_text, read_json, read_yaml, sha256_text, write_json, write_yaml


def test_atomic_write_and_hash(tmp_path):
    path = tmp_path / "x.txt"
    atomic_write_text(path, "hello")
    assert path.read_text() == "hello"
    assert sha256_text("hello").startswith("sha256:")
    atomic_write_text(path, "world")
    assert path.read_text() == "world"


def test_json_yaml_round_trip(tmp_path):
    data = {"case_id": "case_001", "items": [1, 2]}
    jp = tmp_path / "data.json"
    yp = tmp_path / "data.yaml"
    write_json(jp, data)
    write_yaml(yp, data)
    assert read_json(jp) == data
    assert read_yaml(yp) == data


def test_file_lock_append(tmp_path):
    lock_path = tmp_path / "timeline.lock"
    target = tmp_path / "timeline.jsonl"
    with FileLock(lock_path):
        with target.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"event": "created"}) + "\n")
    assert "created" in target.read_text()


def test_blob_store(tmp_path):
    store = BlobStore(tmp_path / "blobs")
    digest, path = store.put(b"abc", suffix=".txt")
    assert digest == sha256_text("abc")
    assert path.exists()
    assert path.read_bytes() == b"abc"
