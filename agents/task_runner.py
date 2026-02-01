"""
Task Runner - Executes planned actions and reports results

This is the engine that DOES the work. It:
1. Takes a plan from TaskPlanner
2. Executes each action in order
3. Handles dependencies between actions
4. Reports progress and results
5. Handles errors gracefully
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from agents.task_planner import TaskPlan, PlannedAction, ActionType
from agents.action_executor import ActionExecutor, get_executor

logger = logging.getLogger(__name__)


class TaskRunner:
    """
    Executes task plans and manages the execution lifecycle.
    """
    
    def __init__(
        self, 
        ollama_client,
        workspace_path: str = None,
        on_progress: Callable[[str, Dict], None] = None
    ):
        """
        Initialize the task runner.
        
        Args:
            ollama_client: Ollama client for LLM calls
            workspace_path: Default workspace path
            on_progress: Callback for progress updates
        """
        self.ollama_client = ollama_client
        self.workspace_path = workspace_path or os.getcwd()
        self.executor = get_executor(workspace_path)
        self.on_progress = on_progress
        
        # Execution state
        self.current_plan: Optional[TaskPlan] = None
        self.execution_log: List[Dict[str, Any]] = []
        
    def _report_progress(self, message: str, data: Dict[str, Any] = None):
        """Report progress to callback if available"""
        logger.info(message)
        if self.on_progress:
            self.on_progress(message, data or {})
    
    def execute_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """
        Execute a complete task plan.
        
        Args:
            plan: The TaskPlan to execute
            
        Returns:
            Execution results
        """
        self.current_plan = plan
        plan.status = "executing"
        
        results = {
            "task": plan.task,
            "workspace": plan.workspace,
            "started_at": datetime.now().isoformat(),
            "actions_completed": 0,
            "actions_failed": 0,
            "action_results": [],
            "outputs": [],
            "status": "in_progress"
        }
        
        self._report_progress(f"🚀 Starting execution: {plan.task}", {"plan": plan.task})
        
        # Execute each action in order
        for i, action in enumerate(plan.actions):
            # Check dependencies
            if not self._check_dependencies(action, plan.actions):
                action.status = "failed"
                action.result = {"error": "Dependencies not met"}
                results["actions_failed"] += 1
                continue
            
            # Execute the action
            action.status = "in_progress"
            self._report_progress(
                f"⚡ Step {i+1}/{len(plan.actions)}: {action.description}",
                {"action": action.action_type.value, "step": i+1}
            )
            
            try:
                result = self._execute_action(action, plan)
                action.result = result
                
                if result.get("success", False):
                    action.status = "completed"
                    results["actions_completed"] += 1
                    
                    # Collect outputs
                    if result.get("output"):
                        results["outputs"].append(result["output"])
                    if result.get("content"):
                        results["outputs"].append(result["content"][:500])
                else:
                    action.status = "failed"
                    results["actions_failed"] += 1
                
                results["action_results"].append({
                    "action": action.action_type.value,
                    "description": action.description,
                    "status": action.status,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Action failed: {e}")
                action.status = "failed"
                action.result = {"success": False, "error": str(e)}
                results["actions_failed"] += 1
        
        # Finalize results
        results["ended_at"] = datetime.now().isoformat()
        results["status"] = "completed" if results["actions_failed"] == 0 else "completed_with_errors"
        plan.status = results["status"]
        
        self._report_progress(
            f"✅ Execution complete: {results['actions_completed']} succeeded, {results['actions_failed']} failed",
            results
        )
        
        return results
    
    def _check_dependencies(self, action: PlannedAction, all_actions: List[PlannedAction]) -> bool:
        """Check if an action's dependencies are met"""
        for dep_index in action.depends_on:
            if dep_index < len(all_actions):
                dep_action = all_actions[dep_index]
                if dep_action.status != "completed":
                    return False
        return True
    
    def _execute_action(self, action: PlannedAction, plan: TaskPlan) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.action_type
        params = action.parameters
        
        # Map action types to execution methods
        executors = {
            ActionType.READ_FILE: self._exec_read_file,
            ActionType.CREATE_FILE: self._exec_create_file,
            ActionType.EDIT_FILE: self._exec_edit_file,
            ActionType.DELETE_FILE: self._exec_delete_file,
            ActionType.RUN_COMMAND: self._exec_run_command,
            ActionType.RUN_PYTHON: self._exec_run_python,
            ActionType.RUN_TESTS: self._exec_run_tests,
            ActionType.GIT_COMMIT: self._exec_git_commit,
            ActionType.GIT_PUSH: self._exec_git_push,
            ActionType.RESEARCH: self._exec_research,
            ActionType.ANALYZE_CODE: self._exec_analyze_code,
            ActionType.GENERATE_CODE: self._exec_generate_code,
            ActionType.CREATE_AGENT: self._exec_create_agent,
            ActionType.RESPOND: self._exec_respond,
        }
        
        executor_func = executors.get(action_type)
        if executor_func:
            return executor_func(params, plan)
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}
    
    # ==================== ACTION EXECUTORS ====================
    
    def _exec_read_file(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Read a file"""
        path = params.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(plan.workspace, path)
        return self.executor.read_file(path)
    
    def _exec_create_file(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Create a file"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        if not os.path.isabs(path):
            path = os.path.join(plan.workspace, path)
        
        # If content is empty but we have a task, use LLM to generate content
        if not content and params.get("generate"):
            content = self._generate_file_content(path, params.get("task", ""), plan)
        
        return self.executor.create_file(path, content)
    
    def _exec_edit_file(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Edit a file"""
        path = params.get("path", "")
        old_content = params.get("old_content", params.get("old", ""))
        new_content = params.get("new_content", params.get("new", ""))
        
        if not os.path.isabs(path):
            path = os.path.join(plan.workspace, path)
        
        return self.executor.edit_file(path, old_content, new_content)
    
    def _exec_delete_file(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Delete a file"""
        path = params.get("path", "")
        if not os.path.isabs(path):
            path = os.path.join(plan.workspace, path)
        
        try:
            if os.path.exists(path):
                os.remove(path)
                return {"success": True, "path": path}
            return {"success": False, "error": "File not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _exec_run_command(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Run a shell command"""
        command = params.get("command", "")
        cwd = params.get("cwd", plan.workspace)
        return self.executor.run_command(command, cwd=cwd)
    
    def _exec_run_python(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Run Python code"""
        code = params.get("code", "")
        return self.executor.run_python(code, cwd=plan.workspace)
    
    def _exec_run_tests(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Run tests"""
        test_path = params.get("path", ".")
        framework = params.get("framework", "pytest")
        return self.executor.run_tests(test_path, framework)
    
    def _exec_git_commit(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Commit to git"""
        message = params.get("message", "Auto-commit by Abby")
        self.executor.git_add(".", plan.workspace)
        return self.executor.git_commit(message, plan.workspace)
    
    def _exec_git_push(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Push to git"""
        return self.executor.git_push(plan.workspace)
    
    def _exec_research(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Research a topic"""
        from agents.research_toolkit import get_research_toolkit
        
        topic = params.get("topic", "")
        depth = params.get("depth", "standard")
        
        research = get_research_toolkit()
        knowledge = research.research_topic(topic, depth)
        
        return {
            "success": True,
            "topic": topic,
            "summary": knowledge.summary,
            "key_facts": knowledge.key_facts[:10],
            "sources": [s.source for s in knowledge.sources[:5]]
        }
    
    def _exec_analyze_code(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Analyze code in a workspace"""
        workspace = params.get("workspace", plan.workspace)
        
        # Gather file information
        files = []
        for root, dirs, filenames in os.walk(workspace):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'venv', '.venv']]
            
            for filename in filenames:
                if filename.endswith(('.py', '.js', '.ts', '.kt', '.java', '.html', '.css', '.json', '.yaml')):
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, workspace)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        files.append({
                            "path": rel_path,
                            "size": len(content),
                            "lines": content.count('\n'),
                            "preview": content[:500]
                        })
                    except:
                        pass
            
            if len(files) >= 50:  # Limit
                break
        
        return {
            "success": True,
            "workspace": workspace,
            "files_found": len(files),
            "files": files[:20]  # Return top 20
        }
    
    def _exec_generate_code(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Generate code using LLM"""
        task = params.get("task", plan.task)
        file_path = params.get("path", "")
        language = params.get("language", "python")
        
        prompt = f"""Generate {language} code for the following task:

{task}

Requirements:
- Write complete, working code
- Include proper error handling
- Add helpful comments
- Follow best practices for {language}

Respond with ONLY the code, no explanations."""

        try:
            response = self.ollama_client.chat(
                messages=[
                    {"role": "system", "content": f"You are an expert {language} developer. Generate clean, working code."},
                    {"role": "user", "content": prompt}
                ],
                model=os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            )
            
            code = response.get("message", {}).get("content", "")
            
            # Clean up code (remove markdown if present)
            if "```" in code:
                import re
                code_match = re.search(r'```(?:\w+)?\n(.*?)```', code, re.DOTALL)
                if code_match:
                    code = code_match.group(1)
            
            result = {"success": True, "code": code, "language": language}
            
            # If file path specified, create the file
            if file_path:
                if not os.path.isabs(file_path):
                    file_path = os.path.join(plan.workspace, file_path)
                self.executor.create_file(file_path, code)
                result["file_created"] = file_path
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _exec_create_agent(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Create a new agent with automatic knowledge building"""
        from agents.agent_factory import AgentFactory
        from agents.research_toolkit import get_research_toolkit
        
        role = params.get("role", "assistant")
        domain = params.get("domain", "general")
        seniority = params.get("seniority", "senior")
        
        try:
            # Research the domain to build knowledge
            research = get_research_toolkit()
            
            self._report_progress(f"🔬 Researching {domain} to build agent expertise...")
            
            # Research multiple aspects
            subtopics = params.get("subtopics", [
                f"{domain} best practices",
                f"{domain} common patterns",
                f"{domain} tools and frameworks"
            ])
            
            knowledge = research.acquire_domain_expertise(domain, subtopics)
            
            # Create knowledge base file
            knowledge_file = f"{domain.lower().replace(' ', '_')}_knowledge.yaml"
            knowledge_path = os.path.join(
                os.path.dirname(__file__), 
                "knowledge", 
                knowledge_file
            )
            
            # Build knowledge YAML
            knowledge_content = self._build_knowledge_yaml(domain, knowledge)
            self.executor.create_file(knowledge_path, knowledge_content)
            
            self._report_progress(f"📚 Created knowledge base: {knowledge_file}")
            
            return {
                "success": True,
                "role": role,
                "domain": domain,
                "knowledge_file": knowledge_file,
                "topics_researched": len(knowledge)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _exec_respond(self, params: Dict, plan: TaskPlan) -> Dict[str, Any]:
        """Generate a text response (no action)"""
        return {"success": True, "output": "Response generated"}
    
    def _generate_file_content(self, path: str, task: str, plan: TaskPlan) -> str:
        """Generate file content using LLM"""
        ext = os.path.splitext(path)[1]
        language = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".kt": "Kotlin",
            ".java": "Java",
            ".html": "HTML",
            ".css": "CSS"
        }.get(ext, "code")
        
        prompt = f"Generate {language} code for: {task}\n\nFile: {path}"
        
        try:
            response = self.ollama_client.chat(
                messages=[
                    {"role": "system", "content": f"You are a {language} expert. Generate clean, working code."},
                    {"role": "user", "content": prompt}
                ],
                model=os.getenv("DEFAULT_MODEL", "qwen2.5:latest")
            )
            return response.get("message", {}).get("content", "")
        except:
            return f"# TODO: Implement {task}"
    
    def _build_knowledge_yaml(self, domain: str, knowledge: Dict) -> str:
        """Build a YAML knowledge base from researched knowledge"""
        import yaml
        
        knowledge_data = {
            f"{domain.lower().replace(' ', '_')}_expertise": {
                "domain": domain,
                "generated_at": datetime.now().isoformat(),
                "topics": {}
            }
        }
        
        for topic, data in knowledge.items():
            topic_data = {
                "summary": data.summary if hasattr(data, 'summary') else str(data),
                "key_facts": data.key_facts[:10] if hasattr(data, 'key_facts') else [],
                "sources": [s.source for s in data.sources[:5]] if hasattr(data, 'sources') else []
            }
            knowledge_data[f"{domain.lower().replace(' ', '_')}_expertise"]["topics"][topic] = topic_data
        
        return yaml.dump(knowledge_data, default_flow_style=False, allow_unicode=True)
