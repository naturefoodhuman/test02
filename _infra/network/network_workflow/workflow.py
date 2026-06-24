# Arena.ai Agent Mode - Execution Lead Engineer
# Created at: 2026-06-23 18:15:00 CST

import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..search.searxng_client import SearXNGProvider
from ..extract import ExtractorChain, Crawl4AIProvider, TrafilaturaProvider
from ..privacy_gateway import build_privacy_gateway, PrivacyContext
from ..local_rag.store import RAGStore
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
        # Pass the specific sub-configs to providers
        self.search_provider = SearXNGProvider(config=self.config.search.searxng)
        
        # Initialize ExtractorChain with values from config
        crawl_provider = Crawl4AIProvider(config=self.config.extract.crawl4ai)
        self.extractor = ExtractorChain(providers=[
            crawl_provider,
            TrafilaturaProvider()
        ])
        self.privacy_gateway = build_privacy_gateway(config=self.config)
        self.sanitizer = InputSanitizer()
        
        # Initialize RAGStore with values from config
        rag_cfg = self.config.local_rag
        self.rag_store = RAGStore(
            db_path=rag_cfg.rag_db,
            chunk_size_tokens=rag_cfg.chunk_size_tokens,
            chunk_overlap_tokens=rag_cfg.chunk_overlap_tokens
        )

    async def execute(self, query: str, mode: str = "research") -> WorkflowResult:
        """
        执行完整搜索流：
        1. Query 清洗 (Sanitizer)
        2. 搜索 (Search)
        3. 提取 (Extract)
        4. 脱敏 (PrivacyGateway)
        5. 入库 (RAG)
        6. 返回带引用的结果
        """
        logger.info(f"Starting network workflow for query: {query} (mode: {mode})")
        
        # 1. Input Sanitization
        # Fix: sanitizer.sanitize needs source_url
        sanitized_content = self.sanitizer.sanitize(query, source_url="user_input")
        sanitized_query = sanitized_content.text

        
        # 2. Search
        search_results = await self.search_provider.search(sanitized_query)
        if not search_results:
            return WorkflowResult(
                query=query,
                processed_query=sanitized_query,
                anonymized_content="No results found.",
                citations=[],
                tokens_removed=0,
                mode=mode
            )

        # 3. Extract (Top K results)
        # Limit to fetch_top_k from config
        top_k = self.config.search.searxng.fetch_top_k
        targets = search_results[:top_k]
        
        extracted_docs = await self.extractor.extract_batch([t.url for t in targets])
        
        # Combine extracted content with metadata
        combined_raw_text = ""
        citations = []
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                source_meta = targets[i]
                combined_raw_text += f"\n--- Source: {source_meta.title} ({source_meta.url}) ---\n"
                combined_raw_text += doc.content
                citations.append({
                    "title": source_meta.title,
                    "url": source_meta.url,
                    "snippet": source_meta.snippet
                })

        # 4. Privacy Gateway (Anonymization)
        # Choose privacy level based on mode
        # PrivacyGateway.process handles L1-L7 and is async
        ctx = PrivacyContext(mode="full" if mode == "research" else "light", source_url="network_workflow")
        gateway_result = await self.privacy_gateway.process(combined_raw_text, ctx=ctx)
        
        # 5. Local RAG Store (Async add)
        # Note: rag_store.add_document is currently synchronous in the E9 implementation
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                # Store anonymized version of each doc individually for better RAG
                doc_privacy_result = await self.privacy_gateway.process(doc.content, ctx=ctx)
                self.rag_store.add_document(
                    content=doc_privacy_result.text,
                    metadata={
                        "url": targets[i].url,
                        "title": targets[i].title,
                        "mode": mode,
                        "query": sanitized_query
                    }
                )

        return WorkflowResult(
            query=query,
            processed_query=sanitized_query,
            anonymized_content=gateway_result.text,
            citations=citations,
            tokens_removed=len(gateway_result.detections),
            mode=mode
        )
