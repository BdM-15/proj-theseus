"""
Test suite for user query prompts (Branch 010 Phase 1)

Tests specialized response formatting via user_prompt parameter.
"""

import pytest
import asyncio
from pathlib import Path
from lightrag.base import QueryParam
from src.core.prompt_loader import load_prompt


class TestPromptLoading:
    """Test prompt file loading"""

    def test_proposal_outline_loads(self):
        """Test proposal outline prompt loads successfully"""
        prompt = load_prompt("user_queries/proposal_outline_generation")
        assert prompt is not None
        assert len(prompt) > 0
        assert "proposal outline" in prompt.lower()

    def test_compliance_assessment_loads(self):
        """Test compliance assessment prompt loads successfully"""
        prompt = load_prompt("user_queries/compliance_assessment")
        assert prompt is not None
        assert "shipley" in prompt.lower() or "compliance" in prompt.lower()

    def test_generate_qfg_loads(self):
        """Test QFG prompt loads successfully"""
        prompt = load_prompt("user_queries/generate_qfg")
        assert prompt is not None
        assert "question" in prompt.lower()

    def test_win_theme_loads(self):
        """Test win theme prompt loads successfully"""
        prompt = load_prompt("user_queries/win_theme_identification")
        assert prompt is not None
        assert "win theme" in prompt.lower() or "differentiat" in prompt.lower()


class TestPromptStructure:
    """Validate prompt content structure"""

    def test_proposal_outline_structure(self):
        """Validate proposal outline prompt has required sections"""
        prompt = load_prompt("user_queries/proposal_outline_generation")
        
        # Check for key structural elements
        assert "volume" in prompt.lower()
        assert "page" in prompt.lower()
        assert "evaluation" in prompt.lower()

    def test_compliance_assessment_structure(self):
        """Validate compliance prompt has scoring framework"""
        prompt = load_prompt("user_queries/compliance_assessment")
        
        # Check for Shipley scoring elements
        assert "score" in prompt.lower()
        assert "requirement" in prompt.lower()
        assert any(x in prompt.lower() for x in ["compliant", "compliance", "gap"])

    def test_qfg_structure(self):
        """Validate QFG prompt has question formatting"""
        prompt = load_prompt("user_queries/generate_qfg")
        
        # Check for QFG elements
        assert "question" in prompt.lower()
        assert "ambiguity" in prompt.lower() or "clarification" in prompt.lower()
        assert "rfp" in prompt.lower()

    def test_win_theme_structure(self):
        """Validate win theme prompt has strategic elements"""
        prompt = load_prompt("user_queries/win_theme_identification")
        
        # Check for strategic analysis elements
        assert "win theme" in prompt.lower() or "theme" in prompt.lower()
        assert "evaluation factor" in prompt.lower()
        assert any(x in prompt.lower() for x in ["differentiat", "competitive", "advantage"])


class TestQueryParamIntegration:
    """Test QueryParam integration (no server required)"""

    def test_query_param_with_user_prompt(self):
        """Test QueryParam accepts user_prompt parameter"""
        prompt = load_prompt("user_queries/proposal_outline_generation")
        
        # Create QueryParam with user_prompt
        query_param = QueryParam(
            mode="hybrid",
            user_prompt=prompt
        )
        
        assert query_param.user_prompt == prompt
        assert query_param.mode == "hybrid"

    def test_all_prompts_with_query_param(self):
        """Test all prompts can be passed to QueryParam"""
        prompts = [
            "user_queries/proposal_outline_generation",
            "user_queries/compliance_assessment",
            "user_queries/generate_qfg",
            "user_queries/win_theme_identification"
        ]
        
        for prompt_name in prompts:
            prompt = load_prompt(prompt_name)
            query_param = QueryParam(mode="hybrid", user_prompt=prompt)
            assert query_param.user_prompt is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestLiveQueries:
    """
    Integration tests requiring running server
    
    Run with: pytest -m integration
    Requires: python app.py (server running at localhost:9621)
    """

    @pytest.fixture
    async def rag_instance(self):
        """Fixture to get RAG instance (mock for now)"""
        # TODO: Replace with actual RAG instance initialization
        # from src.raganything_server import get_rag_instance
        # return await get_rag_instance()
        pytest.skip("Requires running server - implement after server refactor")

    async def test_proposal_outline_query(self, rag_instance):
        """Test proposal outline generation with live query"""
        prompt = load_prompt("user_queries/proposal_outline_generation")
        
        response = await rag_instance.lightrag.aquery(
            "Generate a proposal outline",
            param=QueryParam(mode="hybrid", user_prompt=prompt)
        )
        
        # Validate response structure
        assert response is not None
        assert len(response) > 0
        # Check for expected output elements
        assert any(x in response.lower() for x in ["volume", "section", "page"])

    async def test_compliance_assessment_query(self, rag_instance):
        """Test compliance assessment with live query"""
        prompt = load_prompt("user_queries/compliance_assessment")
        
        response = await rag_instance.lightrag.aquery(
            "Assess compliance for our proposal",
            param=QueryParam(mode="hybrid", user_prompt=prompt)
        )
        
        # Validate response contains scoring
        assert response is not None
        assert any(x in response.lower() for x in ["score", "compliant", "requirement"])

    async def test_qfg_query(self, rag_instance):
        """Test QFG generation with live query"""
        prompt = load_prompt("user_queries/generate_qfg")
        
        response = await rag_instance.lightrag.aquery(
            "What questions should we ask the government?",
            param=QueryParam(mode="hybrid", user_prompt=prompt)
        )
        
        # Validate response contains questions
        assert response is not None
        assert "?" in response  # Should contain question marks

    async def test_win_theme_query(self, rag_instance):
        """Test win theme identification with live query"""
        prompt = load_prompt("user_queries/win_theme_identification")
        
        response = await rag_instance.lightrag.aquery(
            "What are our win themes?",
            param=QueryParam(mode="hybrid", user_prompt=prompt)
        )
        
        # Validate response contains strategic elements
        assert response is not None
        assert any(x in response.lower() for x in ["theme", "advantage", "factor"])


if __name__ == "__main__":
    # Run unit tests only (no integration tests)
    pytest.main([__file__, "-v", "-m", "not integration"])
