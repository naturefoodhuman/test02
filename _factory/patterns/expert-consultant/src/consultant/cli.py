# 创建/修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 创建时间（北京时间，精确到秒）：2026-06-13 14:35:00 CST
"""专家咨询 CLI 接口。"""
from __future__ import annotations

import argparse
import sys
import os

# 将 src 加入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from consultant.core import ExpertConsultant

def main():
    parser = argparse.ArgumentParser(description="FORGE Factory 专家咨询工具")
    parser.add_argument("query", help="咨询问题")
    parser.add_argument("--expert", default="debt-lawyer", help="指定专家名 (默认: debt-lawyer)")
    parser.add_argument("--index", action="store_true", help="强制重建索引")
    
    args = parser.parse_args()
    
    consultant = ExpertConsultant(args.expert)
    
    if args.index:
        consultant.index(force=True)
        return

    try:
        answer = consultant.ask(args.query)
        print("\n" + "="*50)
        print(f"【专家 ({args.expert}) 的回答】")
        print("="*50)
        print(answer)
        print("="*50)
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
