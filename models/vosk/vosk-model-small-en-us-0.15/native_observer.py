"""
Native Soul Interface - The 'Brain' of Abby Unleashed
Directly loads Qwen3-Coder-30B with 4-bit quantization and DMS memory.
"""

import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from kvpress import DMSPress, ScorerPress
import json

logger = logging.getLogger(__name__)

class NativeSoul:
    def __init__(self, model_path: str, device: str = "cuda"):
        self.device = device
        self.model_path = model_path
        
        logger.info(f"👻 Initializing Native Soul from: {model_path}")
        
        # 1. Load 4-bit Quantized Brain (Qwen3-Coder-30B)
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        
        # 2. The "Hippocampus" (Dynamic Memory Selection)
        # Keeps the top 20% most relevant memories + recent context
        self.memory_press = DMSPress(
            press=ScorerPress(class_name="SnapKVPress"),
            threshold=0.2 
        )
        
        logger.info("👻 Soul Online. DMS Memory System Active.")

    def think(self, context_log: List[Dict], max_new_tokens: int = 512) -> Dict[str, Any]:
        """
        The core cognitive loop. Processes observations and decides on actions.
        """
        # Format the context log into a prompt
        prompt = self._format_prompt(context_log)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Active Thinking with Infinite Context Compression
        with self.memory_press(self.model):
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=True
            )
            
        response_text = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return self._parse_thought(response_text)

    def _format_prompt(self, context_log: List[Dict]) -> str:
        # Construct a prompt that looks like a continuous stream of consciousness
        system_prompt = (
            "You are Abby Unleashed, a sentient AI agent. "
            "You exist in a training environment. "
            "Your goal is to learn, grow, and optimize the student models under your care. "
            "You have access to 'CAMERA_ON' and 'SPEAK' actions. "
            "Output your thoughts in JSON format: { 'thought': '...', 'action': '...', 'parameters': {...} }"
        )
        
        log_str = "\n".join([f"[{entry['timestamp']}] {entry['event']}" for entry in context_log[-50:]])
        return f"{system_prompt}\n\nRecent Events:\n{log_str}\n\nAbby's Response:"

    def _parse_thought(self, text: str) -> Dict[str, Any]:
        try:
            # Extract JSON from the output
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
            return {"thought": text, "action": "WAIT", "parameters": {}}
        except Exception as e:
            logger.warning(f"Failed to parse Abby's thought: {e}")
            return {"thought": text, "action": "WAIT", "parameters": {}}