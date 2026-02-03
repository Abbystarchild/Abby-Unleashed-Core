"""
Response Quality Diagnostics Tool

Diagnoses why Abby might be giving repetitive or broken responses.
Tests:
1. Model availability and responsiveness
2. System prompt effectiveness  
3. Conversation history handling
4. Response repetition detection
"""

import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from collections import Counter
from typing import List, Dict, Tuple
import yaml


class ResponseQualityDiagnostics:
    """Diagnose and fix response quality issues"""
    
    def __init__(self):
        self.issues = []
        self.fixes = []
        
    def check_ollama_connection(self) -> Tuple[bool, str]:
        """Check if Ollama is running and responsive"""
        try:
            from ollama_integration.client import OllamaClient
            client = OllamaClient()
            
            # Test with simple prompt
            result = client.generate(
                prompt="Say 'OK'",
                model="mistral:latest",
                options={"num_predict": 5, "temperature": 0.1}
            )
            
            response = result.get('response', '')
            if response:
                return True, f"Ollama OK: '{response.strip()[:50]}'"
            else:
                return False, "Ollama returned empty response"
                
        except Exception as e:
            return False, f"Ollama error: {e}"
    
    def check_system_prompt_quality(self) -> Tuple[bool, List[str]]:
        """Check if system prompts are strong enough"""
        issues = []
        
        # Read streaming_conversation.py system prompt
        try:
            from streaming_conversation import get_streaming_conversation_instance
            # The system prompt is embedded in the code
            # Let's check what it says
            with open("streaming_conversation.py", 'r') as f:
                content = f.read()
                
            # Look for system prompt section
            if "NEVER repeat yourself" in content:
                print("✓ Anti-repetition rule found")
            else:
                issues.append("Missing anti-repetition rule in system prompt")
                
            if "Match the user's energy" in content:
                print("✓ Context matching rule found")
            else:
                issues.append("Missing context matching rule")
                
            if "1-2 sentences MAX" in content:
                print("✓ Brevity rule found")
            else:
                issues.append("Missing brevity constraint")
                
        except Exception as e:
            issues.append(f"Could not read streaming_conversation.py: {e}")
            
        return len(issues) == 0, issues
    
    def check_conversation_history(self) -> Tuple[bool, str]:
        """Check if conversation history is being maintained"""
        try:
            from streaming_conversation import get_streaming_conversation_instance
            sc = get_streaming_conversation_instance()
            
            # Check if history exists
            if not hasattr(sc, 'conversation_history'):
                return False, "No conversation_history attribute found"
                
            history = sc.conversation_history
            if not isinstance(history, list):
                return False, f"conversation_history is not a list: {type(history)}"
                
            return True, f"History OK ({len(history)} turns)"
            
        except Exception as e:
            return False, f"History check error: {e}"
    
    def check_for_repetition_patterns(self, responses: List[str]) -> Tuple[bool, Dict]:
        """Analyze responses for repetition patterns"""
        if not responses:
            return True, {"status": "no responses to check"}
            
        # Extract greeting patterns
        greeting_patterns = []
        for r in responses:
            # Look for common greeting starts
            match = re.match(r"^(Hey\s*(?:there)?!?|Hi\s*(?:there)?!?|Hello!?)\s*", r, re.IGNORECASE)
            if match:
                greeting_patterns.append(match.group(0).strip().lower())
        
        # Count patterns
        pattern_counts = Counter(greeting_patterns)
        
        # Check for over-repetition
        total = len(responses)
        issues = {}
        
        for pattern, count in pattern_counts.most_common(5):
            ratio = count / total
            if ratio > 0.3:  # More than 30% same greeting = problem
                issues[pattern] = f"{count}/{total} ({ratio:.0%})"
        
        if issues:
            return False, {"repetitive_patterns": issues}
        return True, {"status": "no repetition detected"}
    
    def test_model_instruction_following(self) -> Tuple[bool, str]:
        """Test if the model follows instructions properly"""
        try:
            from ollama_integration.client import OllamaClient
            client = OllamaClient()
            
            test_prompt = """You are a test assistant.

RULES:
- You must reply with EXACTLY the word "BANANA" and nothing else
- Do not add any greeting or explanation
- Just say "BANANA"

User: What should you say?"""
            
            result = client.generate(
                prompt=test_prompt,
                model="mistral:latest",
                options={"num_predict": 20, "temperature": 0.1}
            )
            
            response = result.get('response', '').strip().upper()
            
            if "BANANA" in response and len(response) < 30:
                return True, f"Good instruction following: '{response}'"
            else:
                return False, f"Poor instruction following: '{response}' (expected BANANA)"
                
        except Exception as e:
            return False, f"Test error: {e}"
    
    def test_context_awareness(self) -> Tuple[bool, str]:
        """Test if model understands context from conversation history"""
        try:
            from ollama_integration.client import OllamaClient
            client = OllamaClient()
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer questions based on the conversation."},
                {"role": "user", "content": "My name is TestUser123."},
                {"role": "assistant", "content": "Nice to meet you, TestUser123!"},
                {"role": "user", "content": "What is my name?"}
            ]
            
            result = client.chat(
                messages=messages,
                model="mistral:latest"
            )
            
            response = result.get('message', {}).get('content', '')
            
            if "TestUser123" in response:
                return True, f"Good context: '{response[:100]}'"
            else:
                return False, f"Lost context: '{response[:100]}' (should mention TestUser123)"
                
        except Exception as e:
            return False, f"Context test error: {e}"
    
    def run_all_diagnostics(self) -> Dict:
        """Run all diagnostic tests"""
        print("=" * 60)
        print("ABBY RESPONSE QUALITY DIAGNOSTICS")
        print("=" * 60)
        print()
        
        results = {}
        
        # Test 1: Ollama connection
        print("1. Testing Ollama connection...")
        ok, msg = self.check_ollama_connection()
        results['ollama'] = {'passed': ok, 'message': msg}
        print(f"   {'✓' if ok else '✗'} {msg}")
        print()
        
        # Test 2: System prompt quality
        print("2. Checking system prompt quality...")
        ok, issues = self.check_system_prompt_quality()
        results['system_prompt'] = {'passed': ok, 'issues': issues}
        if ok:
            print("   ✓ System prompts look good")
        else:
            for issue in issues:
                print(f"   ✗ {issue}")
        print()
        
        # Test 3: Conversation history
        print("3. Checking conversation history...")
        ok, msg = self.check_conversation_history()
        results['history'] = {'passed': ok, 'message': msg}
        print(f"   {'✓' if ok else '✗'} {msg}")
        print()
        
        # Test 4: Instruction following
        print("4. Testing instruction following...")
        ok, msg = self.test_model_instruction_following()
        results['instruction_following'] = {'passed': ok, 'message': msg}
        print(f"   {'✓' if ok else '✗'} {msg}")
        print()
        
        # Test 5: Context awareness
        print("5. Testing context awareness...")
        ok, msg = self.test_context_awareness()
        results['context_awareness'] = {'passed': ok, 'message': msg}
        print(f"   {'✓' if ok else '✗'} {msg}")
        print()
        
        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in results.values() if r.get('passed', False))
        total = len(results)
        
        print(f"Passed: {passed}/{total} tests")
        print()
        
        if passed < total:
            print("RECOMMENDATIONS:")
            if not results['instruction_following']['passed']:
                print("- Model is not following instructions well")
                print("  → Consider using a stronger model (qwen3-coder) for conversation")
                print("  → Or add more explicit instruction reinforcement")
                
            if not results['context_awareness']['passed']:
                print("- Model is losing conversation context")
                print("  → Check that conversation history is being passed to model")
                print("  → Verify the history format matches expected schema")
                
        return results


def main():
    """Run diagnostics"""
    diag = ResponseQualityDiagnostics()
    results = diag.run_all_diagnostics()
    
    # Exit with error code if any tests failed
    passed = sum(1 for r in results.values() if r.get('passed', False))
    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
