"""Agent task executor - sends commands to Abby"""
import requests
import json
import sys

def send_to_abby(message):
    response = requests.post(
        'http://localhost:8080/api/stream/chat',
        json={'message': message},
        stream=True,
        timeout=300
    )
    
    full_text = ""
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    if data.get('type') == 'text':
                        content = data.get('content', '')
                        print(content, end='', flush=True)
                        full_text += content
                    elif data.get('type') == 'thinking':
                        print(f"\n[THINKING: {data.get('content')}]")
                    elif data.get('type') == 'error':
                        print(f"\n[ERROR: {data.get('content')}]")
                except:
                    pass
    print()
    return full_text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        print(f"Sending: {message}\n")
        print("=" * 50)
        send_to_abby(message)
        print("=" * 50)
    else:
        print("Usage: python agent_task.py <message>")
