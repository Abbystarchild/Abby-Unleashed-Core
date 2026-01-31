"""
Tests for Agent DNA Framework
"""
import pytest
from agents.agent_dna import AgentDNA


def test_agent_dna_creation():
    """Test creating AgentDNA with all required elements"""
    dna = AgentDNA(
        role="Software Developer",
        seniority="Senior",
        domain="Web Development",
        industry_knowledge=["REST APIs", "Microservices"],
        methodologies=["TDD", "Agile"],
        constraints={"budget": "Limited"},
        output_format={"code": "Python", "docs": "Markdown"}
    )
    
    assert dna.role == "Software Developer"
    assert dna.seniority == "Senior"
    assert dna.domain == "Web Development"
    assert len(dna.industry_knowledge) == 2
    assert len(dna.methodologies) == 2


def test_agent_dna_validation_success():
    """Test DNA validation with complete data"""
    dna = AgentDNA(
        role="DevOps Engineer",
        seniority="Staff",
        domain="Cloud",
        industry_knowledge=["AWS", "K8s"],
        methodologies=["GitOps"],
        constraints={"cost": "Low"},
        output_format={"infra": "Terraform"}
    )
    
    assert dna.validate() == True


def test_agent_dna_validation_missing_role():
    """Test DNA validation fails with missing role"""
    dna = AgentDNA(
        role="",
        seniority="Senior",
        domain="Test",
        industry_knowledge=["Test"],
        methodologies=["Test"],
        constraints={"test": "test"},
        output_format={"test": "test"}
    )
    
    with pytest.raises(ValueError, match="Missing role/seniority"):
        dna.validate()


def test_agent_dna_validation_missing_domain():
    """Test DNA validation fails with missing domain"""
    dna = AgentDNA(
        role="Developer",
        seniority="Senior",
        domain="",
        industry_knowledge=[],
        methodologies=["Test"],
        constraints={"test": "test"},
        output_format={"test": "test"}
    )
    
    with pytest.raises(ValueError, match="Missing domain context"):
        dna.validate()


def test_agent_dna_to_dict():
    """Test converting DNA to dictionary"""
    dna = AgentDNA(
        role="Analyst",
        seniority="Mid",
        domain="Data",
        industry_knowledge=["SQL"],
        methodologies=["Analytics"],
        constraints={"time": "Quick"},
        output_format={"report": "PDF"}
    )
    
    dna_dict = dna.to_dict()
    
    assert isinstance(dna_dict, dict)
    assert dna_dict["role"] == "Analyst"
    assert dna_dict["seniority"] == "Mid"


def test_agent_dna_from_dict():
    """Test creating DNA from dictionary"""
    data = {
        "role": "Manager",
        "seniority": "Principal",
        "domain": "Product",
        "industry_knowledge": ["PLG", "Metrics"],
        "methodologies": ["OKRs"],
        "constraints": {"budget": "High"},
        "output_format": {"strategy": "Slides"},
        "persona_id": "test-123",
        "created_at": "2026-01-31T00:00:00",
        "times_used": 5,
        "success_rate": 0.95,
        "last_improved": None
    }
    
    dna = AgentDNA.from_dict(data)
    
    assert dna.role == "Manager"
    assert dna.times_used == 5
    assert dna.success_rate == 0.95


def test_agent_dna_str_representation():
    """Test string representation of DNA"""
    dna = AgentDNA(
        role="Engineer",
        seniority="Junior",
        domain="Backend",
        industry_knowledge=["APIs"],
        methodologies=["REST"],
        constraints={"learning": "Yes"},
        output_format={"code": "Go"}
    )
    
    assert str(dna) == "Junior Engineer (Backend)"
