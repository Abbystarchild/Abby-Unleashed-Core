"""
Intelligent Agent Capabilities for Abby

This module provides the core capabilities that make AI agents effective:
1. Context gathering - understand before acting
2. Work verification - check results after operations  
3. Plan persistence - don't redo work that's already planned
4. File operation verification - confirm file ops succeeded
5. Self-correction - detect and fix mistakes

These are the capabilities that make agents like Copilot effective.
By giving these to Abby, she becomes equally capable.
"""

import os
import re
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class OperationResult:
    """Result of an operation with verification"""
    success: bool
    operation: str
    details: str
    verified: bool = False
    verification_method: str = ""
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class IntelligentAgent:
    """
    Provides intelligent agent capabilities to Abby.
    
    Key Principles (what makes good AI agents effective):
    1. GATHER CONTEXT FIRST - Never act without understanding
    2. VERIFY YOUR WORK - Check that operations succeeded
    3. PERSIST STATE - Don't lose progress or redo work
    4. BE SPECIFIC - Vague actions lead to vague results
    5. SELF-CORRECT - Detect mistakes and fix them
    """
    
    def __init__(self, workspace_path: str = None, session_dir: str = "session_state"):
        self.workspace = Path(workspace_path) if workspace_path else Path.cwd()
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Track what we've done this session
        self.operations_log: List[OperationResult] = []
        self.context_cache: Dict[str, Any] = {}
        self.active_plan_id: Optional[str] = None
        
    # =========================================================================
    # 1. CONTEXT GATHERING - Understand before acting
    # =========================================================================
    
    def gather_context(self, request: str, workspace: str = None) -> Dict[str, Any]:
        """
        Gather all relevant context before taking action.
        
        This is what makes agents effective - understanding the situation
        before jumping into action.
        """
        context = {
            "request": request,
            "workspace": workspace or str(self.workspace),
            "timestamp": datetime.now().isoformat(),
            "existing_files": [],
            "existing_plans": [],
            "related_code": [],
            "project_info": {},
        }
        
        ws_path = Path(workspace) if workspace else self.workspace
        
        # Check if workspace exists and what's in it
        if ws_path.exists():
            context["workspace_exists"] = True
            context["existing_files"] = self._scan_workspace(ws_path)
            context["project_info"] = self._detect_project_type(ws_path)
        else:
            context["workspace_exists"] = False
            
        # Check for existing task plans related to this request
        context["existing_plans"] = self._find_related_plans(request)
        
        # Extract keywords from request for targeted file search
        keywords = self._extract_keywords(request)
        context["keywords"] = keywords
        
        # Find related code files based on keywords
        if context["workspace_exists"]:
            context["related_code"] = self._find_related_code(ws_path, keywords)
            
        self.context_cache[request[:100]] = context
        return context
    
    def _scan_workspace(self, workspace: Path, max_files: int = 200) -> List[Dict]:
        """Scan workspace for existing files"""
        files = []
        count = 0
        
        try:
            for item in workspace.rglob("*"):
                if count >= max_files:
                    break
                    
                # Skip common non-essential directories
                skip_dirs = ['.git', 'node_modules', '__pycache__', '.gradle', 'build', '.idea', 'venv', '.venv']
                if any(skip in str(item) for skip in skip_dirs):
                    continue
                    
                if item.is_file():
                    files.append({
                        "path": str(item.relative_to(workspace)),
                        "name": item.name,
                        "extension": item.suffix,
                        "size": item.stat().st_size if item.exists() else 0,
                    })
                    count += 1
        except Exception as e:
            logger.warning(f"Error scanning workspace: {e}")
            
        return files
    
    def _detect_project_type(self, workspace: Path) -> Dict[str, Any]:
        """Detect what type of project this is"""
        info = {
            "type": "unknown",
            "languages": [],
            "frameworks": [],
            "has_tests": False,
            "has_docs": False,
        }
        
        # Check for common project files
        indicators = {
            "package.json": ("javascript/typescript", "node"),
            "requirements.txt": ("python", None),
            "pyproject.toml": ("python", None),
            "build.gradle.kts": ("kotlin", "gradle"),
            "build.gradle": ("java/kotlin", "gradle"),
            "Cargo.toml": ("rust", "cargo"),
            "go.mod": ("go", "go modules"),
            "pom.xml": ("java", "maven"),
            "Gemfile": ("ruby", "bundler"),
        }
        
        for file, (lang, framework) in indicators.items():
            if (workspace / file).exists():
                if lang not in info["languages"]:
                    info["languages"].append(lang)
                if framework and framework not in info["frameworks"]:
                    info["frameworks"].append(framework)
                    
        # Check for React Native / KMP
        if (workspace / "android").exists() or (workspace / "androidApp").exists():
            info["frameworks"].append("android")
        if (workspace / "ios").exists() or (workspace / "iosMain").exists():
            info["frameworks"].append("ios")
        if (workspace / "shared").exists():
            info["frameworks"].append("multiplatform")
            
        # Check for tests
        test_patterns = ["test", "tests", "spec", "__tests__", "androidTest"]
        for pattern in test_patterns:
            if list(workspace.rglob(f"*{pattern}*")):
                info["has_tests"] = True
                break
                
        # Check for docs
        doc_patterns = ["README.md", "docs/", "documentation/", "*.md"]
        for pattern in doc_patterns:
            if list(workspace.glob(pattern)):
                info["has_docs"] = True
                break
                
        # Determine primary type
        if "kotlin" in str(info["languages"]) or "multiplatform" in info["frameworks"]:
            info["type"] = "kotlin-multiplatform"
        elif "javascript/typescript" in info["languages"]:
            info["type"] = "javascript"
        elif "python" in info["languages"]:
            info["type"] = "python"
        elif info["languages"]:
            info["type"] = info["languages"][0]
            
        return info
    
    def _extract_keywords(self, request: str) -> List[str]:
        """Extract important keywords from request"""
        # Remove common words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'create', 'build', 'make', 'add', 'implement', 'please', 'want', 'need'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', request.lower())
        
        # Filter and return unique keywords
        keywords = []
        for word in words:
            if word not in stop_words and len(word) > 2 and word not in keywords:
                keywords.append(word)
                
        return keywords[:20]  # Limit to top 20
    
    def _find_related_code(self, workspace: Path, keywords: List[str], max_files: int = 10) -> List[Dict]:
        """Find code files related to keywords"""
        related = []
        
        code_extensions = {'.py', '.kt', '.java', '.ts', '.tsx', '.js', '.jsx', '.swift'}
        
        try:
            for item in workspace.rglob("*"):
                if len(related) >= max_files:
                    break
                    
                if not item.is_file() or item.suffix not in code_extensions:
                    continue
                    
                # Skip non-essential directories
                skip_dirs = ['.git', 'node_modules', '__pycache__', '.gradle', 'build']
                if any(skip in str(item) for skip in skip_dirs):
                    continue
                
                # Check if filename matches any keyword
                name_lower = item.stem.lower()
                matches = [kw for kw in keywords if kw in name_lower]
                
                if matches:
                    related.append({
                        "path": str(item.relative_to(workspace)),
                        "name": item.name,
                        "matched_keywords": matches,
                        "relevance": len(matches),
                    })
                    
        except Exception as e:
            logger.warning(f"Error finding related code: {e}")
            
        # Sort by relevance
        related.sort(key=lambda x: x["relevance"], reverse=True)
        return related
    
    # =========================================================================
    # 2. PLAN PERSISTENCE - Don't redo work
    # =========================================================================
    
    def _find_related_plans(self, request: str) -> List[Dict]:
        """Find existing plans that might be related to this request"""
        related = []
        plans_dir = self.session_dir / "task_plans"
        
        if not plans_dir.exists():
            return related
            
        # Extract keywords from request
        request_keywords = set(self._extract_keywords(request))
        
        for plan_file in plans_dir.glob("*.json"):
            try:
                with open(plan_file, 'r') as f:
                    plan_data = json.load(f)
                    
                # Check similarity with original request
                plan_keywords = set(self._extract_keywords(plan_data.get("original_request", "")))
                
                # Calculate overlap
                overlap = len(request_keywords & plan_keywords)
                similarity = overlap / max(len(request_keywords), 1)
                
                if similarity > 0.3:  # 30% keyword overlap
                    related.append({
                        "id": plan_data["id"],
                        "file": str(plan_file),
                        "summary": plan_data.get("summary", "")[:100],
                        "similarity": similarity,
                        "completed": plan_data.get("completed_tasks", 0),
                        "total": plan_data.get("total_tasks", 0),
                        "created": plan_data.get("created_at", ""),
                    })
            except Exception as e:
                logger.warning(f"Error reading plan {plan_file}: {e}")
                
        # Sort by similarity
        related.sort(key=lambda x: x["similarity"], reverse=True)
        return related
    
    def get_or_create_plan(self, request: str, decomposer) -> Tuple[Any, bool]:
        """
        Get an existing plan or create a new one.
        
        Returns:
            (plan, is_new) - The plan and whether it was newly created
        """
        # Check for existing related plans
        related = self._find_related_plans(request)
        
        # If we have a highly similar plan (>60%), reuse it
        for plan_info in related:
            if plan_info["similarity"] > 0.6:
                logger.info(f"Found existing plan {plan_info['id']} with {plan_info['similarity']:.0%} similarity")
                
                # Load the plan
                try:
                    with open(plan_info["file"], 'r') as f:
                        plan_data = json.load(f)
                    
                    from task_decomposer import TaskPlan
                    plan = TaskPlan.from_dict(plan_data)
                    self.active_plan_id = plan.id
                    return plan, False
                except Exception as e:
                    logger.warning(f"Error loading plan: {e}")
                    
        # No suitable existing plan, create new one
        plan = decomposer.decompose(request)
        self.active_plan_id = plan.id
        return plan, True
    
    def load_plan(self, plan_id: str) -> Optional[Any]:
        """Load a specific plan by ID"""
        plan_file = self.session_dir / "task_plans" / f"{plan_id}.json"
        
        if not plan_file.exists():
            return None
            
        try:
            with open(plan_file, 'r') as f:
                plan_data = json.load(f)
            
            from task_decomposer import TaskPlan
            return TaskPlan.from_dict(plan_data)
        except Exception as e:
            logger.error(f"Error loading plan {plan_id}: {e}")
            return None
    
    # =========================================================================
    # 3. WORK VERIFICATION - Confirm operations succeeded
    # =========================================================================
    
    def verify_file_operation(self, operation: str, path: str, expected_content: str = None) -> OperationResult:
        """
        Verify that a file operation succeeded.
        
        This is crucial - don't just say you did something, VERIFY it worked.
        """
        result = OperationResult(
            success=False,
            operation=operation,
            details=f"File: {path}",
        )
        
        file_path = Path(path)
        
        if operation == "create":
            if file_path.exists():
                result.success = True
                result.verified = True
                result.verification_method = "file_exists_check"
                result.artifacts.append(str(file_path))
                
                # Verify content if provided
                if expected_content:
                    try:
                        actual = file_path.read_text()
                        if expected_content in actual:
                            result.details += " (content verified)"
                        else:
                            result.details += " (content mismatch)"
                            result.success = False
                    except:
                        pass
            else:
                result.errors.append(f"File does not exist: {path}")
                
        elif operation == "modify":
            if file_path.exists():
                result.success = True
                result.verified = True
                result.verification_method = "file_exists_check"
                # Could also check modification time
            else:
                result.errors.append(f"File does not exist: {path}")
                
        elif operation == "delete":
            if not file_path.exists():
                result.success = True
                result.verified = True
                result.verification_method = "file_not_exists_check"
            else:
                result.errors.append(f"File still exists: {path}")
                
        elif operation == "directory":
            if file_path.is_dir():
                result.success = True
                result.verified = True
                result.verification_method = "directory_exists_check"
            else:
                result.errors.append(f"Directory does not exist: {path}")
                
        self.operations_log.append(result)
        return result
    
    def verify_command_result(self, command: str, expected_output: str = None, 
                             expected_exit_code: int = 0, actual_exit_code: int = None,
                             actual_output: str = None) -> OperationResult:
        """Verify that a command executed successfully"""
        result = OperationResult(
            success=False,
            operation="command",
            details=f"Command: {command[:100]}...",
        )
        
        # Check exit code
        if actual_exit_code is not None:
            if actual_exit_code == expected_exit_code:
                result.success = True
                result.verified = True
                result.verification_method = "exit_code_check"
            else:
                result.errors.append(f"Exit code {actual_exit_code}, expected {expected_exit_code}")
                
        # Check output if provided
        if expected_output and actual_output:
            if expected_output in actual_output:
                result.details += " (output verified)"
            else:
                result.details += " (output mismatch)"
                
        self.operations_log.append(result)
        return result
    
    def verify_all_operations(self) -> Dict[str, Any]:
        """Get summary of all operations and their verification status"""
        total = len(self.operations_log)
        successful = sum(1 for op in self.operations_log if op.success)
        verified = sum(1 for op in self.operations_log if op.verified)
        
        return {
            "total_operations": total,
            "successful": successful,
            "verified": verified,
            "success_rate": successful / total if total > 0 else 1.0,
            "verification_rate": verified / total if total > 0 else 1.0,
            "errors": [
                {"operation": op.operation, "errors": op.errors}
                for op in self.operations_log if op.errors
            ],
        }
    
    # =========================================================================
    # 4. SELF-CORRECTION - Detect and fix mistakes
    # =========================================================================
    
    def detect_issues(self, workspace: str = None) -> List[Dict]:
        """
        Detect potential issues in the workspace.
        
        This helps catch mistakes before they become problems.
        """
        issues = []
        ws_path = Path(workspace) if workspace else self.workspace
        
        if not ws_path.exists():
            issues.append({
                "type": "missing_workspace",
                "severity": "high",
                "message": f"Workspace does not exist: {ws_path}",
                "fix": "Create the workspace directory",
            })
            return issues
            
        # Check for common issues
        
        # 1. Empty source directories
        src_dirs = ["src", "app", "lib", "source"]
        for src_dir in src_dirs:
            src_path = ws_path / src_dir
            if src_path.is_dir() and not any(src_path.iterdir()):
                issues.append({
                    "type": "empty_source_dir",
                    "severity": "medium",
                    "message": f"Source directory is empty: {src_dir}",
                    "fix": "Add source files or remove empty directory",
                })
                
        # 2. Missing config files for detected project type
        project_info = self._detect_project_type(ws_path)
        
        if "node" in project_info["frameworks"]:
            if not (ws_path / "package.json").exists():
                issues.append({
                    "type": "missing_config",
                    "severity": "high",
                    "message": "Node project missing package.json",
                    "fix": "Run npm init or create package.json",
                })
                
        if "kotlin" in str(project_info["languages"]):
            if not (ws_path / "build.gradle.kts").exists() and not (ws_path / "build.gradle").exists():
                issues.append({
                    "type": "missing_config",
                    "severity": "high", 
                    "message": "Kotlin project missing build.gradle",
                    "fix": "Create Gradle build configuration",
                })
                
        # 3. Check for incomplete task plans
        plans_dir = self.session_dir / "task_plans"
        if plans_dir.exists():
            for plan_file in plans_dir.glob("*.json"):
                try:
                    with open(plan_file, 'r') as f:
                        plan_data = json.load(f)
                    
                    completed = plan_data.get("completed_tasks", 0)
                    total = plan_data.get("total_tasks", 0)
                    
                    if total > 0 and completed < total:
                        progress = completed / total * 100
                        issues.append({
                            "type": "incomplete_plan",
                            "severity": "low",
                            "message": f"Task plan {plan_data['id']} is {progress:.0f}% complete ({completed}/{total} tasks)",
                            "fix": f"Resume work on plan {plan_data['id']}",
                        })
                except:
                    pass
                    
        return issues
    
    def suggest_next_action(self, context: Dict = None) -> Dict[str, Any]:
        """
        Suggest the best next action based on current state.
        
        This helps Abby stay focused and productive.
        """
        suggestion = {
            "action": None,
            "reason": "",
            "priority": "medium",
            "details": {},
        }
        
        # Check for incomplete plans first
        if self.active_plan_id:
            plan = self.load_plan(self.active_plan_id)
            if plan:
                next_tasks = plan.get_next_tasks()
                if next_tasks:
                    suggestion = {
                        "action": "continue_plan",
                        "reason": f"Resume work on plan {plan.id}",
                        "priority": "high",
                        "details": {
                            "plan_id": plan.id,
                            "next_tasks": [t.title for t in next_tasks],
                            "progress": plan.get_progress(),
                        },
                    }
                    return suggestion
                    
        # Check for issues
        issues = self.detect_issues()
        high_severity = [i for i in issues if i["severity"] == "high"]
        
        if high_severity:
            issue = high_severity[0]
            suggestion = {
                "action": "fix_issue",
                "reason": issue["message"],
                "priority": "high",
                "details": {
                    "issue": issue,
                    "fix": issue.get("fix", ""),
                },
            }
            return suggestion
            
        # Default: gather more context
        suggestion = {
            "action": "gather_context",
            "reason": "Need more information before proceeding",
            "priority": "medium",
            "details": {},
        }
        
        return suggestion


# Global instance
_agent_instance: Optional[IntelligentAgent] = None

def get_intelligent_agent(workspace: str = None) -> IntelligentAgent:
    """Get or create the global intelligent agent instance"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = IntelligentAgent(workspace_path=workspace)
    elif workspace and str(_agent_instance.workspace) != workspace:
        _agent_instance = IntelligentAgent(workspace_path=workspace)
        
    return _agent_instance
