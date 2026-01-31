"""
Ollama Integration Client
"""
import os
import logging
import requests
from typing import Dict, Any, Optional, Generator
import json


logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with Ollama API
    """
    
    def __init__(self, host: Optional[str] = None):
        """
        Initialize Ollama client
        
        Args:
            host: Ollama host URL (default: from env or localhost)
        """
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.base_url = f"{self.host}/api"
        
        logger.info(f"Initialized Ollama client: {self.host}")
    
    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:latest",
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        Generate response from Ollama
        
        Args:
            prompt: User prompt
            model: Model name
            system: System prompt
            stream: Whether to stream response
            **kwargs: Additional generation parameters
            
        Returns:
            Response dictionary or generator if streaming
        """
        url = f"{self.base_url}/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        
        if system:
            payload["system"] = system
        
        try:
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {"error": str(e)}
    
    def _stream_generate(self, url: str, payload: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """
        Stream generate responses
        
        Args:
            url: API endpoint
            payload: Request payload
            
        Yields:
            Response chunks
        """
        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {"error": str(e)}
    
    def chat(
        self,
        messages: list,
        model: str = "qwen2.5:latest",
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any] | Generator[Dict[str, Any], None, None]:
        """
        Chat with Ollama using conversation history
        
        Args:
            messages: List of message dictionaries
            model: Model name
            stream: Whether to stream response
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary or generator if streaming
        """
        url = f"{self.base_url}/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {"error": str(e)}
    
    def list_models(self) -> Dict[str, Any]:
        """
        List available models
        
        Returns:
            Dictionary with model list
        """
        url = f"{self.base_url}/tags"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return {"models": [], "error": str(e)}
    
    def is_model_available(self, model: str) -> bool:
        """
        Check if a model is available
        
        Args:
            model: Model name
            
        Returns:
            True if available
        """
        models_data = self.list_models()
        
        if "error" in models_data:
            return False
        
        model_names = [m.get("name", "") for m in models_data.get("models", [])]
        
        return model in model_names
    
    def pull_model(self, model: str) -> Dict[str, Any]:
        """
        Pull a model from Ollama library
        
        Args:
            model: Model name
            
        Returns:
            Response dictionary
        """
        url = f"{self.base_url}/pull"
        
        payload = {"name": model}
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return {"error": str(e)}
