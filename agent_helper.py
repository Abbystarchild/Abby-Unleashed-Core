"""
Agent Helper - I (Copilot) use this to communicate with Abby without interfering with her server
"""
import requests
import json
import sys
import time

def send_task(message):
    """Send a task to Abby and collect streaming response"""
    print(f"\n{'='*60}")
    print("SENDING TASK TO ABBY")
    print(f"{'='*60}")
    print(f"Task length: {len(message)} chars\n")
    
    try:
        response = requests.post(
            'http://localhost:8080/api/stream/chat',
            json={'message': message},
            stream=True,
            timeout=300
        )
        
        full_response = ""
        print("ABBY'S RESPONSE:")
        print("-" * 40)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        event_type = data.get('type', '')
                        content = data.get('content', '')
                        
                        if event_type == 'text':
                            print(content, end='', flush=True)
                            full_response += content
                        elif event_type == 'thinking':
                            print(f"\n[THINKING: {content}]")
                        elif event_type == 'error':
                            print(f"\n[ERROR: {content}]")
                        elif event_type == 'done':
                            print('\n[DONE]')
                    except json.JSONDecodeError:
                        pass
        
        print("\n" + "-" * 40)
        return full_response
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_task_plans():
    """Check what task plans exist"""
    import os
    plans_dir = "session_state/task_plans"
    if os.path.exists(plans_dir):
        files = os.listdir(plans_dir)
        print(f"\nTask plans found: {len(files)}")
        for f in sorted(files, key=lambda x: os.path.getmtime(os.path.join(plans_dir, x)), reverse=True):
            path = os.path.join(plans_dir, f)
            mtime = time.ctime(os.path.getmtime(path))
            print(f"  - {f} (modified: {mtime})")
    else:
        print("No task plans directory found")

if __name__ == "__main__":
    # The full SafeConnect task
    safeconnect_task = """Build a dating app called SafeConnect with:

1. RPG tavern-themed discovery page where user avatars sit at tables based on compatibility scores
2. Full character creator with pixel art style avatar customization (hair, face, clothing, accessories)  
3. Geolocation-based matching - show users within configurable radius, sort by distance and compatibility
4. SafeConnect monitored dates feature - users can schedule real meetups with optional safety escort service integration
5. Full iOS and Android mobile app support using React Native
6. Backend API with user authentication, matching algorithm, chat system, and date scheduling
7. Admin dashboard for monitoring user reports, safety incidents, and platform analytics

Make it production ready with proper error handling, testing, and documentation."""

    print("Checking existing task plans first...")
    check_task_plans()
    
    print("\n\nSending SafeConnect task to Abby...")
    response = send_task(safeconnect_task)
    
    print("\n\nChecking task plans after request...")
    check_task_plans()
