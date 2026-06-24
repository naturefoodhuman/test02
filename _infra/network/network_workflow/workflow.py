# Arena.ai Agent Mode - Execution Lead Engineer
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
        crawl_provider = Crawl4AIProvider(config=self.config.extract.crawl4ai)
        self.extractor = ExtractorChain(providers=[crawl_provider, TrafilaturaProvider()])
        self.privacy_gateway = build_privacy_gateway(config=self.config)
        self.sanitizer = InputSanitizer()
        self.rag_store = RAGStore(db_path=self.config.local_rag.rag_db)

    async def execute(self, query: str, mode: str = "research") -> WorkflowResult:
        logger.info(f"Starting network workflow for: {query}")
        sanitized = self.sanitizer.sanitize(query, source_url="user_input").text
        
        results = await self.search_provider.search(sanitized)
        if not results:
            return WorkflowResult(query=query, processed_query=sanitized, anonymized_content="No results found.", citations=[], tokens_removed=0, mode=mode)

        print(f"[INFO] SearXNG found {len(results)} results.")
        top_k = self.config.search.searxng.fetch_top_k
        targets = results[:top_k]
        
        extracted_docs = []
        for i, t in enumerate(targets, 1):
            print(f"[INFO] ({i}/{len(targets)}) Extracting: {t.url}")
            doc = await self.extractor.extract(t.url)
            # Fallback to snippet if extraction failed or content is empty
            if not doc.content:
                print(f"      [Fallback to snippet]")
                doc.content = t.snippet
            extracted_docs.append(doc)

        combined_text = ""
        citations = []
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                source_meta = targets[i]
                combined_text += f"\n--- Source: {source_meta.title} ({source_meta.url}) ---\n"
                combined_text += doc.content
                citations.append({"title": source_meta.title, "url": source_meta.url})

        ctx = PrivacyContext(mode="full" if mode=="research" else "light", source_url="network_workflow")
        gw_res = await self.privacy_gateway.process(combined_text, ctx=ctx)
        
        # Async add to RAG (simplified sync call in loop as store is sync)
        for i, doc in enumerate(extracted_docs):
            if doc.content:
                res = await self.privacy_gateway.process(doc.content, ctx=ctx)
                self.rag_store.add_document(
                    DocumentInput(
                        content=res.text,
                        source_url=targets[i].url,
                        title=targets[i].title,
                        metadata={"query": sanitized}
                    )
                )

        return WorkflowResult(query=query, processed_query=sanitized, anonymized_content=gw_res.text, 
                              citations=citations, tokens_removed=len(gw_res.detections), mode=mode)
