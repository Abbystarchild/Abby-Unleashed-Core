"""
Input validation for Abby Unleashed
Provides security and type safety for user inputs
"""
import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TaskInput(BaseModel):
    """Validated task input"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    description: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Task description"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional task context"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate and sanitize task description"""
        # Remove any potential script injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Task description contains potentially unsafe content")
        
        return v


class OllamaConfig(BaseModel):
    """Validated Ollama configuration"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    host: str = Field(
        default="http://localhost:11434",
        description="Ollama host URL"
    )
    timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Request timeout in seconds"
    )
    connect_timeout: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Connection timeout in seconds"
    )
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host URL format"""
        if not v.startswith(('http://', 'https://')):
            v = f"http://{v}"
        
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9\-\.]+(:\d+)?$'
        if not re.match(url_pattern, v):
            raise ValueError(f"Invalid Ollama host URL: {v}")
        
        return v


class PathConfig(BaseModel):
    """Validated file path configuration"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    path: str = Field(..., description="File or directory path")
    must_exist: bool = Field(default=False, description="Path must exist")
    must_be_dir: bool = Field(default=False, description="Path must be a directory")
    must_be_file: bool = Field(default=False, description="Path must be a file")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate and sanitize file path"""
        # Resolve to absolute path
        p = Path(v).resolve()
        base_dir = Path.cwd().resolve()
        
        # Check for path traversal - ensure path is within base directory
        try:
            p.relative_to(base_dir)
        except ValueError:
            # Path is outside base directory
            raise ValueError(f"Path is outside allowed directory: {v}")
        
        return str(p)
    
    def model_post_init(self, __context: Any) -> None:
        """Additional validation after initialization"""
        p = Path(self.path)
        
        if self.must_exist and not p.exists():
            raise ValueError(f"Path does not exist: {self.path}")
        
        if self.must_be_dir and not p.is_dir():
            raise ValueError(f"Path is not a directory: {self.path}")
        
        if self.must_be_file and not p.is_file():
            raise ValueError(f"Path is not a file: {self.path}")


class EnvironmentConfig(BaseModel):
    """Validated environment configuration"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='allow')
    
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama host URL"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    stt_model: str = Field(
        default="base.en",
        description="Speech-to-text model"
    )
    tts_voice: str = Field(
        default="en_US-amy-medium",
        description="Text-to-speech voice"
    )
    wake_word: str = Field(
        default="hey abby",
        min_length=3,
        max_length=50,
        description="Wake word phrase"
    )
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @classmethod
    def from_env(cls) -> "EnvironmentConfig":
        """Load configuration from environment variables"""
        return cls(
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            stt_model=os.getenv("STT_MODEL", "base.en"),
            tts_voice=os.getenv("TTS_VOICE", "en_US-amy-medium"),
            wake_word=os.getenv("WAKE_WORD", "hey abby")
        )


def validate_task_input(description: str, context: Optional[Dict[str, Any]] = None) -> TaskInput:
    """
    Validate and sanitize task input
    
    Args:
        description: Task description
        context: Optional context dictionary
        
    Returns:
        Validated TaskInput
        
    Raises:
        ValueError: If validation fails
    """
    return TaskInput(description=description, context=context)


def validate_ollama_config(
    host: Optional[str] = None,
    timeout: int = 120,
    connect_timeout: int = 5
) -> OllamaConfig:
    """
    Validate Ollama configuration
    
    Args:
        host: Ollama host URL
        timeout: Request timeout
        connect_timeout: Connection timeout
        
    Returns:
        Validated OllamaConfig
        
    Raises:
        ValueError: If validation fails
    """
    return OllamaConfig(
        host=host or "http://localhost:11434",
        timeout=timeout,
        connect_timeout=connect_timeout
    )


def validate_path(
    path: str,
    must_exist: bool = False,
    must_be_dir: bool = False,
    must_be_file: bool = False
) -> PathConfig:
    """
    Validate file path
    
    Args:
        path: File or directory path
        must_exist: Path must exist
        must_be_dir: Path must be a directory
        must_be_file: Path must be a file
        
    Returns:
        Validated PathConfig
        
    Raises:
        ValueError: If validation fails
    """
    return PathConfig(
        path=path,
        must_exist=must_exist,
        must_be_dir=must_be_dir,
        must_be_file=must_be_file
    )
