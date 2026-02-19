#!/usr/bin/env python3
"""Quick test for Abby Unleashed"""
import requests

print("Testing Abby Unleashed connection...")

try:
    # Test Ollama
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": "Say hello in one sentence.",
            "stream": False
        },
        timeout=30
    )
    
    if r.status_code == 200:
        response = r.json().get('response', '')
        print(f"✓ Ollama working! Response: {response}")
    else:
        print(f"✗ Error: Status {r.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Make sure Ollama is running: ollama serve")
