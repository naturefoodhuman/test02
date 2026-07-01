# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-07-01 00:00:00

"""Clipboard adapter with test-friendly fake support."""

from __future__ import annotations

import subprocess


class ClipboardAdapter:
    def copy_text(self, text: str) -> None:
        subprocess.run(["pbcopy"], input=text, text=True, check=True)

    def paste_text(self) -> str:
        return subprocess.check_output(["pbpaste"], text=True)


class FakeClipboardAdapter:
    def __init__(self, initial: str = ""):
        self.value = initial

    def copy_text(self, text: str) -> None:
        self.value = text

    def paste_text(self) -> str:
        return self.value
