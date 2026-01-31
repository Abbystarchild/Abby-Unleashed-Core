"""
Tests for Persona Library
"""
import pytest
import os
import tempfile
from agents.agent_dna import AgentDNA
from persona_library.library_manager import PersonaLibrary


@pytest.fixture
def temp_library_path():
    """Create temporary library path"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        path = f.name
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_dna():
    """Create sample DNA"""
    return AgentDNA(
        role="Backend Developer",
        seniority="Senior",
        domain="E-commerce",
        industry_knowledge=["Payment systems", "APIs"],
        methodologies=["Microservices", "TDD"],
        constraints={"security": "PCI-DSS"},
        output_format={"code": "Python", "api": "REST"}
    )


def test_persona_library_creation(temp_library_path):
    """Test creating persona library"""
    library = PersonaLibrary(temp_library_path)
    
    assert library.library_path == temp_library_path
    assert len(library.personas) == 0


def test_persona_library_save(temp_library_path, sample_dna):
    """Test saving persona to library"""
    library = PersonaLibrary(temp_library_path)
    
    library.save(sample_dna)
    
    assert len(library.personas) == 1
    assert sample_dna.persona_id in library.personas


def test_persona_library_load(temp_library_path, sample_dna):
    """Test loading personas from file"""
    library = PersonaLibrary(temp_library_path)
    library.save(sample_dna)
    
    # Create new library instance to test loading
    library2 = PersonaLibrary(temp_library_path)
    
    assert len(library2.personas) == 1
    loaded_dna = library2.get(sample_dna.persona_id)
    assert loaded_dna.role == sample_dna.role


def test_persona_library_find_match(temp_library_path, sample_dna):
    """Test finding matching persona"""
    library = PersonaLibrary(temp_library_path)
    library.save(sample_dna)
    
    requirements = {
        "role": "Backend Developer",
        "domain": "E-commerce"
    }
    
    match = library.find_match(requirements)
    
    assert match is not None
    assert match.role == "Backend Developer"


def test_persona_library_find_no_match(temp_library_path, sample_dna):
    """Test when no matching persona exists"""
    library = PersonaLibrary(temp_library_path)
    library.save(sample_dna)
    
    requirements = {
        "role": "Data Scientist",
        "domain": "Machine Learning"
    }
    
    match = library.find_match(requirements)
    
    assert match is None


def test_persona_library_delete(temp_library_path, sample_dna):
    """Test deleting persona"""
    library = PersonaLibrary(temp_library_path)
    library.save(sample_dna)
    
    assert len(library.personas) == 1
    
    library.delete(sample_dna.persona_id)
    
    assert len(library.personas) == 0


def test_persona_library_stats(temp_library_path, sample_dna):
    """Test getting library statistics"""
    library = PersonaLibrary(temp_library_path)
    library.save(sample_dna)
    
    stats = library.get_stats()
    
    assert stats["total_personas"] == 1
    assert "Backend Developer" in stats["roles"]
    assert "E-commerce" in stats["domains"]
