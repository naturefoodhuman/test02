# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
# 创建时间（北京时间）：2026-06-22 19:54:33

"""
Download spaCy models for Privacy Gateway NER (E5-C4-S1-T1).

Default models:
- zh_core_web_sm
- en_core_web_sm

Usage:
    python _infra/network/scripts/download_spacy_models.py
    python _infra/network/scripts/download_spacy_models.py --model zh_core_web_sm
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Sequence

DEFAULT_MODELS = ("zh_core_web_sm", "en_core_web_sm")


def download_models(models: Sequence[str] = DEFAULT_MODELS) -> None:
    """Download requested spaCy models using the active Python interpreter."""
    for model in models:
        print(f"Downloading spaCy model: {model}")
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", model],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download spaCy NER models for FORGE Network")
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Model name to download. Can be passed multiple times. Defaults to zh/en small models.",
    )
    args = parser.parse_args()
    download_models(tuple(args.models or DEFAULT_MODELS))


if __name__ == "__main__":
    main()
