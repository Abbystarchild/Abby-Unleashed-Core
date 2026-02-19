#!/usr/bin/env python3
"""
Response Formatter Patch for Abby Unleashed
Fixes common response formatting issues
"""

def clean_response(text):
    """Clean and format LLM responses"""
    if not text:
        return ""
    
    # Remove excessive newlines
    text = '\n'.join(line for line in text.split('\n') if line.strip())
    
    # Fix common formatting issues
    text = text.replace('\n\n\n', '\n\n')
    text = text.strip()
    
    # Remove markdown artifacts if present
    if text.startswith('```') and text.endswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1])
    
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
        'response': '\n\n\nHello!\n\n\nThis is a test.\n\n\n'
    }
    print(format_for_display(test_response))
