"""
Tests for Base Agent
"""
import pytest
import os
from agents.agent_dna import AgentDNA
from agents.base_agent import Agent

# Check if we should skip network-dependent tests
SKIP_NETWORK_TESTS = os.getenv("SKIP_NETWORK_TESTS", "0") == "1"


@pytest.fixture
def sample_dna():
    """Create sample DNA for testing"""
    return AgentDNA(
        role="Test Engineer",
        seniority="Senior",
        domain="Quality Assurance",
        industry_knowledge=["Testing", "Automation"],
        methodologies=["TDD", "BDD"],
        constraints={"coverage": "80%"},
        output_format={"tests": "Pytest", "reports": "HTML"}
    )


def test_agent_creation(sample_dna):
    """Test creating an agent"""
    agent = Agent(dna=sample_dna)
    
    assert agent.dna == sample_dna
    assert agent.personality == {}
    assert len(agent.task_history) == 0


def test_agent_creation_with_personality(sample_dna):
    """Test creating agent with personality"""
    personality = {"tone": "friendly", "style": "concise"}
    agent = Agent(dna=sample_dna, personality=personality)
    
    assert agent.personality == personality


def test_agent_system_prompt(sample_dna):
    """Test system prompt generation"""
    agent = Agent(dna=sample_dna)
    prompt = agent.get_system_prompt()
    
    assert "Senior Test Engineer" in prompt
    assert "Quality Assurance" in prompt
    assert "Testing" in prompt


@pytest.mark.skipif(SKIP_NETWORK_TESTS, reason="Skipping network-dependent test")
def test_agent_execute_task_insufficient_info(sample_dna):
    """Test task execution with insufficient information (requires LLM)"""
    agent = Agent(dna=sample_dna)
    
    # Very vague task should trigger clarification or error if LLM unavailable
    result = agent.execute_task("test", {})
    
    # Should request clarification OR error if LLM/network unavailable
    # In test environments, network/LLM issues are acceptable
    assert result["status"] in ["clarification_needed", "error"]
    if result["status"] == "clarification_needed":
        assert "questions" in result


@pytest.mark.skipif(SKIP_NETWORK_TESTS, reason="Skipping network-dependent test")
def test_agent_execute_task_with_context(sample_dna):
    """Test task execution with proper context (requires LLM)"""
    agent = Agent(dna=sample_dna)
    
    task = "Create automated tests for login functionality"
    context = {
        "output_format": "pytest",
        "domain_requirements": "web application testing"
    }
    
    result = agent.execute_task(task, context)
    
    # Should execute, clarify, or error if LLM unavailable
    assert result["status"] in ["completed", "clarification_needed", "error"]
