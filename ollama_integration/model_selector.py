"""
Model Selector - Choose best model for task
"""
import logging
from typing import Dict, List, Optional
import yaml
import os


logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Chooses optimal Ollama model based on agent role and task.
    """
    
    def __init__(self, config_path: str = "config/ollama_models.yaml", ollama_client=None):
        """
        Initialize model selector
        
        Args:
            config_path: Path to model configuration
            ollama_client: OllamaClient instance
        """
        self.config_path = config_path
        self.ollama_client = ollama_client
        self.model_preferences = {}
        self.default_model = "qwen2.5:latest"
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load model configuration from file"""
        if not os.path.exists(self.config_path):
            logger.warning(f"Model config not found: {self.config_path}, using defaults")
            self._use_defaults()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.model_preferences = config.get('models', {})
            self.default_model = config.get('default_model', 'qwen2.5:latest')
            
            logger.info(f"Loaded model configuration with {len(self.model_preferences)} categories")
        
        except Exception as e:
            logger.error(f"Error loading model config: {e}")
            self._use_defaults()
    
    def _use_defaults(self):
        """Use default model preferences"""
        self.model_preferences = {
            "code": ["qwen2.5-coder:latest", "deepseek-coder:latest"],
            "reasoning": ["deepseek-r1:latest", "qwen2.5:32b"],
            "general": ["qwen2.5:latest", "llama3.1:latest"],
            "creative": ["llama3.1:latest", "mistral:latest"],
        }
    
    def select_model(self, agent_role: str = "", task_type: str = "") -> str:
        """
        Select optimal model based on role and task
        
        Args:
            agent_role: Agent role description
            task_type: Type of task
            
        Returns:
            Model name
        """
        # Determine task category
        category = self._categorize_task(agent_role, task_type)
        
        # Get models for category
        models = self.model_preferences.get(category, [self.default_model])
        
        # Return first available model
        for model in models:
            if self._is_model_available(model):
                logger.info(f"Selected model: {model} (category: {category})")
                return model
        
        # Fallback to default
        logger.info(f"Using default model: {self.default_model}")
        return self.default_model
    
    def _categorize_task(self, agent_role: str, task_type: str) -> str:
        """
        Categorize task to determine best model type
        
        Args:
            agent_role: Agent role
            task_type: Task type
            
        Returns:
            Category name
        """
        combined = f"{agent_role} {task_type}".lower()
        
        # Check for code-related
        if any(word in combined for word in ["code", "develop", "program", "software", "engineer"]):
            return "code"
        
        # Check for reasoning
        if any(word in combined for word in ["analyze", "research", "strategy", "plan"]):
            return "reasoning"
        
        # Check for creative
        if any(word in combined for word in ["write", "design", "creative", "content"]):
            return "creative"
        
        # Default to general
        return "general"
    
    def _is_model_available(self, model: str) -> bool:
        """
        Check if model is available
        
        Args:
            model: Model name
            
        Returns:
            True if available
        """
        if not self.ollama_client:
            # Assume available if no client
            return True
        
        return self.ollama_client.is_model_available(model)
    
    def get_available_models(self) -> List[str]:
        """
        Get list of all available models
        
        Returns:
            List of model names
        """
        if not self.ollama_client:
            return []
        
        models_data = self.ollama_client.list_models()
        
        if "error" in models_data:
            return []
        
        return [m.get("name", "") for m in models_data.get("models", [])]
