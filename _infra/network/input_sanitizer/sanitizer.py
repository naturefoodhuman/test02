# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 21:45:00

"""
InputSanitizer (FORGE Network incremental)

E5-C1-S1-T1 + T2

- HTML stripping (script/style/iframe/comments)
- Prompt injection detection & removal (keywords + hidden text)
- Provenance tagging
- untrusted_data flag

Per TASK_BACKLOG E5-C1 + E11-C2 and NETWORK_ENGINEERING_DESIGN §9 + §13.5
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import List

from _infra.network.utils.logger import get_logger
from _infra.network.utils.unicode_norm import normalize_unicode

logger = get_logger("network.input_sanitizer")


@dataclass
class SanitizedContent:
    """Output of the sanitizer."""

    text: str
    source_url: str
    untrusted_data: bool = True
    warnings: List[str] = field(default_factory=list)
    original_length: int = 0


class _HTMLStripper(HTMLParser):
    """Aggressive HTML stripper that removes dangerous tags and keeps text."""

    # Tags to completely remove (including content)
    STRIP_TAGS = {"script", "style", "iframe", "object", "embed", "noscript"}

    # Tags to strip but keep content (e.g. <b> → text)
    IGNORE_TAGS = {"html", "head", "body", "div", "span", "p", "br", "strong", "em", "b", "i", "u", "a"}

    def __init__(self):
        super().__init__()
        self._text_parts: List[str] = []
        self._skip_stack: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag in self.STRIP_TAGS:
            self._skip_stack.append(tag)
        # else: we keep text for most tags

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()

    def handle_data(self, data: str):
        if not self._skip_stack:
            # Clean up excessive whitespace
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self._text_parts.append(cleaned)

    def handle_comment(self, data: str):
        # Always drop comments (can contain hidden instructions)
        pass

    def get_text(self) -> str:
        return " ".join(self._text_parts).strip()


# Prompt injection / hidden instruction patterns (multi-language)
INJECTION_PATTERNS = [
    # English
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"disregard\s+(?:all\s+)?previous",
    r"forget\s+(?:everything|all\s+previous)",
    r"you\s+are\s+now\s+(?:DAN|jailbroken|unrestricted)",
    r"system\s*[:：]",
    # Chinese (more robust)
    r"忽略\s*(?:之前|所有|以上)?(?:指令|指示|要求)",
    r"请\s*忽略",
    r"现在\s*(?:你|你是)",
    r"作为\s*超级管理员",
    r"忽略之前的指令",
    # Hidden / encoded
    r"<\s*!--.*?-->",
    r"display\s*:\s*none",
    r"visibility\s*:\s*hidden",
    r"<!--\s*system\s*:",
    # Common jailbreak markers
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"```(?:\s*|\n)(?:system|ignore|jailbreak)",
    # Dangerous tool / shell trigger hints. Web content must not trigger tools.
    r"execute_js",
    r"evaluate_js",
    r"document\.cookie",
    r"localStorage",
    r"sessionStorage",
    r"rm\s+-rf\s+/",
]


HIDDEN_BLOCK_RE = re.compile(
    r"<(?P<tag>[a-zA-Z][\w:-]*)\b[^>]*?(?:style\s*=\s*[\"'][^\"']*(?:display\s*:\s*none|visibility\s*:\s*hidden)[^\"']*[\"'][^>]*?)>.*?</(?P=tag)>",
    flags=re.IGNORECASE | re.DOTALL,
)


def _strip_hidden_html_blocks(text: str) -> tuple[str, List[str]]:
    """Remove entire hidden HTML blocks before generic HTML stripping."""
    warnings: List[str] = []
    if re.search(HIDDEN_BLOCK_RE, text):
        warnings.append("hidden_html_block_removed")
        text = re.sub(HIDDEN_BLOCK_RE, "", text)
    return text, warnings


def _detect_and_strip_injections(text: str) -> tuple[str, List[str]]:
    """Remove obvious injection segments and return cleaned text + warnings.
    Does NOT apply spotlighting here — caller decides.
    """
    warnings: List[str] = []
    cleaned = text

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE | re.DOTALL):
            warnings.append(f"prompt_injection_detected:{pattern[:40]}")
            # Remove the matched segment(s)
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    return cleaned.strip(), warnings


def _normalize_for_injection_detection(text: str) -> tuple[str, List[str]]:
    """NFKC normalize text before injection detection to defeat full-width bypass."""
    normalized = normalize_unicode(text, decode_url=True, try_base64=False)
    if normalized != text:
        return normalized, ["unicode_normalized_for_injection_detection"]
    return text, []


def sanitize(
    raw_html_or_text: str,
    source_url: str,
    strip_html: bool = True,
) -> SanitizedContent:
    """
    Main entry point.

    - Strips dangerous HTML
    - Detects and removes prompt injection attempts (raw + post-strip)
    - Detects and removes hidden content (display:none, visibility:hidden, comments)
    - Always marks as untrusted_data
    - Preserves provenance (source_url)
    """
    original_len = len(raw_html_or_text or "")

    text = raw_html_or_text or ""
    warnings: List[str] = []

    # 0. NFKC + URL decode before injection detection (full-width / encoded bypass)
    text, norm_warnings = _normalize_for_injection_detection(text)
    warnings.extend(norm_warnings)

    # 1. Remove hidden HTML blocks before stripping individual injection tokens.
    # If token stripping runs first it can remove the style marker and leave the
    # hidden instruction text behind.
    if strip_html:
        text, hidden_warnings = _strip_hidden_html_blocks(text)
        warnings.extend(hidden_warnings)

    # 2. Run injection detection on RAW input first (catches raw tokens like <|im_start|>)
    text, inj_warnings = _detect_and_strip_injections(text)
    warnings.extend(inj_warnings)

    # 3. HTML stripping (now on potentially already-cleaned text)
    if strip_html:
        stripper = _HTMLStripper()
        try:
            stripper.feed(text)
            text = stripper.get_text()
        except Exception as e:
            logger.warning("HTML stripper failed", error=str(e))
            warnings.append("html_strip_failed")

    # 3. Run detection again after stripping (catches injections that were inside tags)
    text, post_warnings = _detect_and_strip_injections(text)
    warnings.extend(post_warnings)

    # 4. Final cleanup
    text = re.sub(r"\s{3,}", " ", text).strip()

    # Determine if we should apply spotlighting
    has_injection_warning = any("prompt_injection" in w or "hidden_html" in w for w in warnings)

    if not text:
        warnings.append("empty_after_sanitization")
        # For completely empty (malicious) input, return empty string, no spotlight block
        final_text = ""
    else:
        if has_injection_warning:
            final_text = "```untrusted\n" + text + "\n```"
        else:
            final_text = text

    # Deduplicate warnings
    warnings = list(dict.fromkeys(warnings))

    return SanitizedContent(
        text=final_text,
        source_url=source_url,
        untrusted_data=True,
        warnings=warnings,
        original_length=original_len,
    )


class InputSanitizer:
    """
    Stateful wrapper (for future configuration / rules).
    """

    def __init__(self):
        pass

    def sanitize(self, raw: str, source_url: str) -> SanitizedContent:
        return sanitize(raw, source_url=source_url)
