# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-24 14:48:00
import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from ..search.searxng_client import SearXNGProvider
from ..extract import ExtractorChain, Crawl4AIProvider, TrafilaturaProvider
from ..privacy_gateway import build_privacy_gateway, PrivacyContext
from ..local_rag.store import RAGStore
from ..local_rag.models import DocumentInput
from ..input_sanitizer.sanitizer import InputSanitizer
from ..config_loader import load_network_config

logger = logging.getLogger(__name__)

class WorkflowResult(BaseModel):
    query: str
    processed_query: str
    anonymized_content: str
    citations: List[Dict[str, str]]
    tokens_removed: int
    mode: str

class NetworkWorkflow:
    def __init__(self, config=None):
        self.config = config or load_network_config()
        self.search_provider = SearXNGProvider(config=self.config.search.searxng)
        self.extractor = ExtractorChain(providers=[Crawl4AIProvider(config=self.config.extract.crawl4ai), TrafilaturaProvider()])
        self.privacy_gateway = build_privacy_gateway(config=self.config)
        self.sanitizer = InputSanitizer()
        self.rag_store = RAGStore(db_path=self.config.local_rag.rag_db)

    async def execute(self, query: str, mode: str = "research") -> WorkflowResult:
        sanitized = self.sanitizer.sanitize(query, source_url="user_input").text
        results = await self.search_provider.search(sanitized)
        if not results:
            return WorkflowResult(query=query, processed_query=sanitized, anonymized_content="No results found.", citations=[], tokens_removed=0, mode=mode)

        print(f"[INFO] SearXNG found {len(results)} results.")
        targets = results[:self.config.search.searxng.fetch_top_k]
        
        extracted_docs = await self.extractor.extract_batch([t.url for t in targets])
        for i, doc in enumerate(extracted_docs):
            if not doc.content:
                print(f"      [Fallback to snippet for {targets[i].url}]")
                doc.content = targets[i].snippet

        combined_text = ""
        citations = []
        for i, doc in enumerate(extracted_docs):
            combined_text += f"\n--- Source: {targets[i].title} ({targets[i].url}) ---\n{doc.content}\n"
            citations.append({"title": targets[i].title, "url": targets[i].url})

        ctx = PrivacyContext(mode="full" if mode=="research" else "light", source_url="network_workflow")
        gw_res = await self.privacy_gateway.process(combined_text, ctx=ctx)
        
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                try:
                    res = await self.privacy_gateway.process(doc.content, ctx=ctx)
                    self.rag_store.add_document(DocumentInput(content=res.text, source_url=targets[i].url, title=targets[i].title))
                except Exception as e:
                    print(f"[WARNING] RAG failed for {targets[i].url}: {e}")

        return WorkflowResult(query=query, processed_query=sanitized, anonymized_content=gw_res.text, citations=citations, tokens_removed=len(gw_res.detections), mode=mode)
