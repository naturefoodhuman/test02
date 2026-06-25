# 创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
# 创建时间（北京时间）：2026-06-25 00:00:00

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from _infra.network.network_workflow.workflow import NetworkWorkflow, WorkflowResult
from _infra.network.search.models import SearchResult
from _infra.network.extract.models import ExtractResult

def test_workflow_execution_basic():
    async def run_test():
        mock_config = MagicMock()
        mock_config.search.searxng.fetch_top_k = 2
        
        with patch("_infra.network.network_workflow.workflow.MultiSourceSearchOrchestrator") as MockSearch,              patch("_infra.network.network_workflow.workflow.ExtractorChain") as MockExtract,              patch("_infra.network.network_workflow.workflow.build_privacy_gateway") as MockGatewayFactory,              patch("_infra.network.network_workflow.workflow.RAGStore") as MockRAG,              patch("_infra.network.network_workflow.workflow.load_network_config", return_value=mock_config):
            
            mock_search_inst = MockSearch.return_value
            mock_search_inst.search = AsyncMock(return_value=[
                SearchResult(title="Result 1", url="https://a.com", snippet="Snippet 1", score=1.0),
                SearchResult(title="Result 2", url="https://b.com", snippet="Snippet 2", score=0.9)
            ])
            
            mock_extract_inst = MockExtract.return_value
            mock_extract_inst.extract_batch = AsyncMock(return_value=[
                ExtractResult(url="https://a.com", content="Content from A", mode="markdown"),
                ExtractResult(url="https://b.com", content="Content from B", mode="markdown")
            ])
            
            mock_gateway_inst = MockGatewayFactory.return_value
            mock_gateway_result = MagicMock()
            mock_gateway_result.text = "Anonymized text with [PII]"
            mock_gateway_result.detections = [{"type": "PERSON"}]
            mock_gateway_inst.process = AsyncMock(return_value=mock_gateway_result)
            
            workflow = NetworkWorkflow(config=mock_config)
            result = await workflow.execute("search for John Doe", mode="research")
            
            assert isinstance(result, WorkflowResult)
            assert result.query == "search for John Doe"
            assert "Anonymized" in result.anonymized_content
            assert len(result.citations) == 2
            assert result.citations[0]["url"] == "https://a.com"
            
            mock_search_inst.search.assert_called_once()
            mock_extract_inst.extract_batch.assert_called_once()
            assert mock_gateway_inst.process.call_count >= 1
            assert MockRAG.return_value.add_document.call_count == 2

    asyncio.run(run_test())

def test_workflow_no_results():
    async def run_test():
        mock_config = MagicMock()
        with patch("_infra.network.network_workflow.workflow.MultiSourceSearchOrchestrator") as MockSearch,              patch("_infra.network.network_workflow.workflow.load_network_config", return_value=mock_config):
            
            mock_search_inst = MockSearch.return_value
            mock_search_inst.search = AsyncMock(return_value=[])
            
            workflow = NetworkWorkflow(config=mock_config)
            result = await workflow.execute("nonexistent query")
            
            assert result.anonymized_content == "No results found."
            assert len(result.citations) == 0
    
    asyncio.run(run_test())
