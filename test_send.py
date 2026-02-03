"""Quick test script to send messages to Abby"""
import requests
import json
import sys

def send(msg):
    print(f'Sending: {msg}')
    print('-' * 40)
    try:
        r = requests.post('http://localhost:8080/api/stream/chat', json={'message': msg}, stream=True, timeout=120)
        for line in r.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    t = data.get('type')
                    c = data.get('content', '')
                    if t == 'text':
                        print(c, end='', flush=True)
                    elif t == 'thinking':
                        print(f"\n[THINKING: {c}]")
                    elif t == 'error':
                        print(f"\n[ERROR: {c}]")
    except Exception as e:
        print(f'Error: {e}')
    print('\n' + '-' * 40)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        send(' '.join(sys.argv[1:]))
    else:
        send("continue with task 1")
