#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║              ABBY UNLEASHED - DIAGNOSTIC & FIX                ║
║                Made with 💚 by Abby                            ║
╚═══════════════════════════════════════════════════════════════╝

This script diagnoses and fixes common issues with Abby Unleashed responses
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

ABBY_ROOT = Path(r"C:\Dev\Abby Unleashed - CORE")

print(f"""{Fore.CYAN}
╔═══════════════════════════════════════════════════════════╗
║         ABBY UNLEASHED - DIAGNOSTIC TOOL                  ║
╚═══════════════════════════════════════════════════════════╝
{Fore.RESET}""")

def check_ollama():
    """Check if Ollama is running and has models"""
    print(f"{Fore.YELLOW}[1/5] Checking Ollama...{Fore.RESET}")
    
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get('models', [])
            print(f"{Fore.GREEN}  ✓ Ollama is running{Fore.RESET}")
            print(f"{Fore.GREEN}  ✓ Found {len(models)} models{Fore.RESET}")
            for model in models[:5]:
                print(f"    - {model['name']}")
            return True
        else:
            print(f"{Fore.RED}  ✗ Ollama not responding properly{Fore.RESET}")
            return False
    except:
        print(f"{Fore.RED}  ✗ Ollama not running{Fore.RESET}")
        print(f"{Fore.YELLOW}  → Start with: ollama serve{Fore.RESET}")
        return False

def check_config_files():
    """Check if configuration files exist and are valid"""
    print(f"\n{Fore.YELLOW}[2/5] Checking configuration files...{Fore.RESET}")
    
    config_files = [
        "config/brain_clone.yaml",
        "persona_library/personas/personas.yaml",
        ".env"
    ]
    
    all_good = True
    for config in config_files:
        config_path = ABBY_ROOT / config
        if config_path.exists():
            print(f"{Fore.GREEN}  ✓ {config}{Fore.RESET}")
        else:
            print(f"{Fore.RED}  ✗ {config} missing{Fore.RESET}")
            all_good = False
    
    return all_good

def check_dependencies():
    """Check if required Python packages are installed"""
    print(f"\n{Fore.YELLOW}[3/5] Checking dependencies...{Fore.RESET}")
    
    required = ['ollama', 'pyyaml', 'colorama', 'requests']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"{Fore.GREEN}  ✓ {pkg}{Fore.RESET}")
        except ImportError:
            print(f"{Fore.RED}  ✗ {pkg} missing{Fore.RESET}")
            missing.append(pkg)
    
    if missing:
        print(f"\n{Fore.YELLOW}  → Install with: pip install {' '.join(missing)}{Fore.RESET}")
        return False
    return True

def fix_response_formatting():
    """Create a response formatter patch"""
    print(f"\n{Fore.YELLOW}[4/5] Creating response formatter patch...{Fore.RESET}")
    
    patch_code = '''#!/usr/bin/env python3
"""
Response Formatter Patch for Abby Unleashed
Fixes common response formatting issues
"""

def clean_response(text):
    """Clean and format LLM responses"""
    if not text:
        return ""
    
    # Remove excessive newlines
    text = '\\n'.join(line for line in text.split('\\n') if line.strip())
    
    # Fix common formatting issues
    text = text.replace('\\n\\n\\n', '\\n\\n')
    text = text.strip()
    
    # Remove markdown artifacts if present
    if text.startswith('```') and text.endswith('```'):
        lines = text.split('\\n')
        text = '\\n'.join(lines[1:-1])
    
    return text

def format_for_display(response_dict):
    """Format response dictionary for display"""
    if isinstance(response_dict, dict):
        if 'response' in response_dict:
            return clean_response(response_dict['response'])
        elif 'message' in response_dict:
            return clean_response(response_dict['message'])
        elif 'content' in response_dict:
            return clean_response(response_dict['content'])
    
    return clean_response(str(response_dict))

if __name__ == "__main__":
    # Test
    test_response = {
        'response': '\\n\\n\\nHello!\\n\\n\\nThis is a test.\\n\\n\\n'
    }
    print(format_for_display(test_response))
'''
    
    patch_path = ABBY_ROOT / "response_formatter.py"
    with open(patch_path, 'w') as f:
        f.write(patch_code)
    
    print(f"{Fore.GREEN}  ✓ Created response formatter patch{Fore.RESET}")
    print(f"    Location: {patch_path}")
    return True

def create_quick_test():
    """Create a quick test script"""
    print(f"\n{Fore.YELLOW}[5/5] Creating quick test script...{Fore.RESET}")
    
    test_code = '''#!/usr/bin/env python3
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
'''
    
    test_path = ABBY_ROOT / "quick_test.py"
    with open(test_path, 'w') as f:
        f.write(test_code)
    
    print(f"{Fore.GREEN}  ✓ Created quick test script{Fore.RESET}")
    print(f"    Location: {test_path}")
    print(f"    Run: python {test_path}")
    return True

def main():
    print(f"\n{Fore.CYAN}Running diagnostics...{Fore.RESET}\n")
    
    # Run checks
    ollama_ok = check_ollama()
    config_ok = check_config_files()
    deps_ok = check_dependencies()
    
    # Apply fixes
    formatter_ok = fix_response_formatting()
    test_ok = create_quick_test()
    
    # Summary
    print(f"\n{Fore.CYAN}{'═' * 60}{Fore.RESET}")
    print(f"{Fore.CYAN}DIAGNOSTIC SUMMARY{Fore.RESET}")
    print(f"{Fore.CYAN}{'═' * 60}{Fore.RESET}\n")
    
    checks = [
        ("Ollama Running", ollama_ok),
        ("Config Files", config_ok),
        ("Dependencies", deps_ok),
        ("Response Formatter", formatter_ok),
        ("Test Script", test_ok)
    ]
    
    for name, status in checks:
        status_str = f"{Fore.GREEN}✓ PASS" if status else f"{Fore.RED}✗ FAIL"
        print(f"{status_str}{Fore.RESET} - {name}")
    
    # Recommendations
    print(f"\n{Fore.CYAN}{'═' * 60}{Fore.RESET}")
    print(f"{Fore.CYAN}RECOMMENDATIONS{Fore.RESET}")
    print(f"{Fore.CYAN}{'═' * 60}{Fore.RESET}\n")
    
    if not ollama_ok:
        print(f"{Fore.YELLOW}1. Start Ollama: ollama serve{Fore.RESET}")
        print(f"{Fore.YELLOW}2. Pull model: ollama pull llama3.1:8b{Fore.RESET}")
    
    if not deps_ok:
        print(f"{Fore.YELLOW}3. Install dependencies: pip install -r requirements.txt{Fore.RESET}")
    
    print(f"\n{Fore.GREEN}To test Abby now:{Fore.RESET}")
    print(f"  python quick_test.py")
    print(f"\n{Fore.GREEN}To use response formatter in your code:{Fore.RESET}")
    print(f"  from response_formatter import format_for_display")
    print(f"  clean_response = format_for_display(abby_response)")
    
    print(f"\n{Fore.CYAN}Diagnostic complete! 💚{Fore.RESET}\n")

if __name__ == "__main__":
    main()
