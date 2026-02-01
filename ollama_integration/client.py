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
    
    def __init__(self, host: Optional[str] = None, timeout: int = 120, connect_timeout: int = 5):
        """
        Initialize Ollama client
        
        Args:
            host: Ollama host URL (default: from env or localhost)
            timeout: Request timeout in seconds (default: 120)
            connect_timeout: Connection timeout in seconds (default: 5)
        """
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        # Validate host format
        if not self.host.startswith(('http://', 'https://')):
            self.host = f"http://{self.host}"
        
        self.base_url = f"{self.host}/api"
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        
        logger.info(f"Initialized Ollama client: {self.host}")
    
    def health_check(self) -> bool:
        """
        Check if Ollama server is healthy and responding
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
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
        
        # Default generation options to prevent repetitive/verbose responses
        default_options = {
            "temperature": 0.8,
            "repeat_penalty": 1.8,
            "repeat_last_n": 128,
            "top_k": 40,
            "top_p": 0.9,
            "stop": ["\n\n\n", "---"],
        }
        
        # Merge with any provided options
        options = {**default_options, **kwargs.get('options', {})}
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": options,
        }
        
        # Add other kwargs except 'options'
        for k, v in kwargs.items():
            if k != 'options':
                payload[k] = v
        
        if system:
            payload["system"] = system
        
        try:
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=(self.connect_timeout, self.timeout)
                )
                response.raise_for_status()
                return response.json()
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout generating response: {e}")
            return {"error": f"Request timed out after {self.timeout}s"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {"error": f"Failed to connect to Ollama at {self.host}"}
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
            with requests.post(
                url, 
                json=payload, 
                stream=True, 
                timeout=(self.connect_timeout, self.timeout)
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            yield data
                        except json.JSONDecodeError:
                            continue
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout streaming response: {e}")
            yield {"error": f"Request timed out after {self.timeout}s"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            yield {"error": f"Failed to connect to Ollama at {self.host}"}
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
        
        # Default generation options to prevent repetitive/verbose responses
        # These can be overridden via kwargs
        default_options = {
            "temperature": 0.8,          # Slightly more creative
            "repeat_penalty": 1.8,       # VERY strong penalty for repetition
            "repeat_last_n": 128,        # Look back further for repetition
            "top_k": 40,                 # Limit token choices
            "top_p": 0.9,                # Nucleus sampling
            "num_predict": 150,          # Shorter responses
            "stop": ["\n\n\n", "---"],  # Stop on multiple newlines
        }
        
        # Merge with any provided options
        options = {**default_options, **kwargs.get('options', {})}
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": options,
        }
        
        # Add any other kwargs except 'options' which we already handled
        for k, v in kwargs.items():
            if k != 'options':
                payload[k] = v
        
        try:
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(
                    url, 
                    json=payload, 
                    timeout=(self.connect_timeout, self.timeout)
                )
                response.raise_for_status()
                return response.json()
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout in chat: {e}")
            return {"error": f"Request timed out after {self.timeout}s"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return {"error": f"Failed to connect to Ollama at {self.host}"}
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
            response = requests.get(url, timeout=self.connect_timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout listing models: {e}")
            return {"models": [], "error": "Request timed out"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error listing models: {e}")
            return {"models": [], "error": f"Failed to connect to Ollama at {self.host}"}
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
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout pulling model: {e}")
            return {"error": "Pull request timed out"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error pulling model: {e}")
            return {"error": f"Failed to connect to Ollama at {self.host}"}
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """
        Check if Ollama service is available
        
        Returns:
            True if service is healthy
        """
        try:
            response = requests.get(self.host, timeout=self.connect_timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
