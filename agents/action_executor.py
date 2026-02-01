"""
Action Executor - Actually DOES things instead of just talking about them

This module gives Abby and her agents the ability to:
- Run shell commands
- Create and edit files
- Execute Python code
- Run tests
- Git operations
- And more...

The key difference: Abby ACTS, not just TALKS.
"""

import os
import subprocess
import logging
import json
import shutil
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes real actions in the system.
    
    This is what makes Abby actually DO things instead of just describing
    what she would do.
    """
    
    # Allowed base paths for file operations (security)
    ALLOWED_PATHS = [
        r"C:\Dev",
        r"C:\Users",
        r"D:\Projects",
        r"D:\Dev",
    ]
    
    # Dangerous commands to block
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "del /f /s /q c:\\",
        "format",
        "shutdown",
        "reboot",
    ]
    
    def __init__(self, workspace_path: str = None):
        """
        Initialize the action executor.
        
        Args:
            workspace_path: Default workspace for operations
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.action_history: List[Dict[str, Any]] = []
        self.dry_run = False  # Set to True to preview actions without executing
        
    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is within allowed directories"""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(allowed) for allowed in self.ALLOWED_PATHS)
    
    def _is_command_safe(self, command: str) -> bool:
        """Check if a command is safe to execute"""
        cmd_lower = command.lower()
        return not any(blocked in cmd_lower for blocked in self.BLOCKED_COMMANDS)
    
    def _log_action(self, action_type: str, details: Dict[str, Any], success: bool, result: Any = None):
        """Log an action for history/audit"""
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details,
            "success": success,
            "result": str(result)[:500] if result else None
        })
    
    # ==================== FILE OPERATIONS ====================
    
    def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Create a new file with the given content.
        
        Args:
            path: File path (relative to workspace or absolute)
            content: File content
            
        Returns:
            Result dictionary
        """
        try:
            # Resolve path
            if not os.path.isabs(path):
                path = os.path.join(self.workspace_path, path)
            
            # Security check
            if not self._is_path_allowed(path):
                return {"success": False, "error": f"Path not allowed: {path}"}
            
            if self.dry_run:
                return {"success": True, "dry_run": True, "would_create": path}
            
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log_action("create_file", {"path": path, "size": len(content)}, True)
            logger.info(f"Created file: {path}")
            
            return {"success": True, "path": path, "size": len(content)}
            
        except Exception as e:
            self._log_action("create_file", {"path": path}, False, str(e))
            logger.error(f"Failed to create file {path}: {e}")
            return {"success": False, "error": str(e)}
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file's contents"""
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.workspace_path, path)
            
            if not self._is_path_allowed(path):
                return {"success": False, "error": f"Path not allowed: {path}"}
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {"success": True, "content": content, "path": path}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """
        Edit a file by replacing content.
        
        Args:
            path: File path
            old_content: Content to find
            new_content: Content to replace with
            
        Returns:
            Result dictionary
        """
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.workspace_path, path)
            
            if not self._is_path_allowed(path):
                return {"success": False, "error": f"Path not allowed: {path}"}
            
            # Read current content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if old content exists
            if old_content not in content:
                return {"success": False, "error": "Content to replace not found in file"}
            
            if self.dry_run:
                return {"success": True, "dry_run": True, "would_edit": path}
            
            # Replace content
            new_file_content = content.replace(old_content, new_content, 1)
            
            # Write back
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
            
            self._log_action("edit_file", {"path": path}, True)
            logger.info(f"Edited file: {path}")
            
            return {"success": True, "path": path}
            
        except Exception as e:
            self._log_action("edit_file", {"path": path}, False, str(e))
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.workspace_path, path)
            
            if not self._is_path_allowed(path):
                return {"success": False, "error": f"Path not allowed: {path}"}
            
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return {"success": True, "path": path, "items": items}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== COMMAND EXECUTION ====================
    
    def run_command(self, command: str, cwd: str = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Run a shell command.
        
        Args:
            command: Command to run
            cwd: Working directory (defaults to workspace)
            timeout: Timeout in seconds
            
        Returns:
            Result with stdout, stderr, return code
        """
        try:
            if not self._is_command_safe(command):
                return {"success": False, "error": "Command blocked for safety"}
            
            cwd = cwd or self.workspace_path
            
            if self.dry_run:
                return {"success": True, "dry_run": True, "would_run": command}
            
            logger.info(f"Executing: {command}")
            
            # Run command
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            self._log_action("run_command", {"command": command, "cwd": cwd}, result.returncode == 0)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            self._log_action("run_command", {"command": command}, False, str(e))
            return {"success": False, "error": str(e)}
    
    def run_python(self, code: str, cwd: str = None) -> Dict[str, Any]:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            cwd: Working directory
            
        Returns:
            Execution result
        """
        try:
            cwd = cwd or self.workspace_path
            
            if self.dry_run:
                return {"success": True, "dry_run": True, "would_run_python": code[:100]}
            
            # Write to temp file and execute
            temp_file = os.path.join(cwd, "_temp_exec.py")
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            try:
                result = self.run_command(f"python {temp_file}", cwd=cwd)
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== GIT OPERATIONS ====================
    
    def git_status(self, repo_path: str = None) -> Dict[str, Any]:
        """Get git status of a repository"""
        repo_path = repo_path or self.workspace_path
        return self.run_command("git status", cwd=repo_path)
    
    def git_add(self, files: str = ".", repo_path: str = None) -> Dict[str, Any]:
        """Stage files for commit"""
        repo_path = repo_path or self.workspace_path
        return self.run_command(f"git add {files}", cwd=repo_path)
    
    def git_commit(self, message: str, repo_path: str = None) -> Dict[str, Any]:
        """Commit staged changes"""
        repo_path = repo_path or self.workspace_path
        # Escape quotes in message
        message = message.replace('"', '\\"')
        return self.run_command(f'git commit -m "{message}"', cwd=repo_path)
    
    def git_push(self, repo_path: str = None) -> Dict[str, Any]:
        """Push commits to remote"""
        repo_path = repo_path or self.workspace_path
        return self.run_command("git push", cwd=repo_path)
    
    # ==================== PROJECT OPERATIONS ====================
    
    def run_tests(self, test_path: str = ".", framework: str = "pytest") -> Dict[str, Any]:
        """
        Run tests for a project.
        
        Args:
            test_path: Path to tests
            framework: Test framework (pytest, unittest, npm)
            
        Returns:
            Test results
        """
        commands = {
            "pytest": f"pytest {test_path} -v",
            "unittest": f"python -m unittest discover {test_path}",
            "npm": "npm test",
            "jest": "npx jest"
        }
        
        command = commands.get(framework)
        if not command:
            return {"success": False, "error": f"Unknown test framework: {framework}"}
        
        return self.run_command(command)
    
    def install_dependencies(self, package_manager: str = "pip") -> Dict[str, Any]:
        """Install project dependencies"""
        commands = {
            "pip": "pip install -r requirements.txt",
            "npm": "npm install",
            "yarn": "yarn install",
            "poetry": "poetry install"
        }
        
        command = commands.get(package_manager)
        if not command:
            return {"success": False, "error": f"Unknown package manager: {package_manager}"}
        
        return self.run_command(command)
    
    # ==================== PARSE ACTION FROM LLM ====================
    
    def parse_and_execute(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse an LLM response for actions and execute them.
        
        Looks for action blocks like:
        ```action:create_file
        path: src/main.py
        content: |
            print("Hello")
        ```
        
        Or command blocks:
        ```bash
        pip install requests
        ```
        
        Returns:
            List of action results
        """
        results = []
        
        # Pattern for action blocks
        action_pattern = r'```action:(\w+)\n(.*?)```'
        for match in re.finditer(action_pattern, llm_response, re.DOTALL):
            action_type = match.group(1)
            action_content = match.group(2)
            
            result = self._execute_action_block(action_type, action_content)
            results.append(result)
        
        # Pattern for bash/shell commands
        bash_pattern = r'```(?:bash|shell|cmd)\n(.*?)```'
        for match in re.finditer(bash_pattern, llm_response, re.DOTALL):
            command = match.group(1).strip()
            for line in command.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    result = self.run_command(line)
                    results.append(result)
        
        # Pattern for Python code execution
        python_pattern = r'```python:execute\n(.*?)```'
        for match in re.finditer(python_pattern, llm_response, re.DOTALL):
            code = match.group(1)
            result = self.run_python(code)
            results.append(result)
        
        return results
    
    def _execute_action_block(self, action_type: str, content: str) -> Dict[str, Any]:
        """Execute a parsed action block"""
        try:
            # Parse YAML-like content
            lines = content.strip().split('\n')
            params = {}
            current_key = None
            current_value = []
            
            for line in lines:
                if line.startswith('  ') and current_key:
                    current_value.append(line[2:] if line.startswith('    ') else line)
                elif ':' in line:
                    if current_key:
                        params[current_key] = '\n'.join(current_value) if current_value else params.get(current_key)
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    value = value.strip()
                    if value and value != '|':
                        params[current_key] = value
                    current_value = []
            
            if current_key and current_value:
                params[current_key] = '\n'.join(current_value)
            
            # Execute based on action type
            if action_type == "create_file":
                return self.create_file(params.get('path', ''), params.get('content', ''))
            elif action_type == "edit_file":
                return self.edit_file(params.get('path', ''), params.get('old', ''), params.get('new', ''))
            elif action_type == "run_command":
                return self.run_command(params.get('command', ''))
            elif action_type == "run_tests":
                return self.run_tests(params.get('path', '.'), params.get('framework', 'pytest'))
            elif action_type == "git_commit":
                self.git_add()
                return self.git_commit(params.get('message', 'Auto-commit'))
            else:
                return {"success": False, "error": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get the history of executed actions"""
        return self.action_history


# Global executor instance
_executor: Optional[ActionExecutor] = None


def get_executor(workspace_path: str = None) -> ActionExecutor:
    """Get or create the global action executor"""
    global _executor
    if _executor is None or (workspace_path and _executor.workspace_path != workspace_path):
        _executor = ActionExecutor(workspace_path)
    return _executor
