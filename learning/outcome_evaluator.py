"""
Outcome evaluator for assessing task execution quality
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OutcomeEvaluator:
    """
    Evaluates outcomes of task executions
    
    Assesses quality, identifies patterns, and generates insights
    """
    
    def __init__(self):
        """Initialize outcome evaluator"""
        self.evaluation_history: List[Dict[str, Any]] = []
        logger.info("Outcome evaluator initialized")
    
    def evaluate_task_outcome(
        self,
        task_id: str,
        task_description: str,
        result: Dict[str, Any],
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a task outcome
        
        Args:
            task_id: Task identifier
            task_description: Task description
            result: Task result
            agent_id: Agent that executed task
            metadata: Optional metadata
            
        Returns:
            Evaluation dictionary
        """
        evaluation = {
            "task_id": task_id,
            "task_description": task_description,
            "agent_id": agent_id,
            "evaluated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Evaluate success
        evaluation["success"] = self._evaluate_success(result)
        
        # Evaluate quality
        evaluation["quality_score"] = self._evaluate_quality(result, task_description)
        
        # Evaluate completeness
        evaluation["completeness_score"] = self._evaluate_completeness(result)
        
        # Overall score
        evaluation["overall_score"] = (
            evaluation["quality_score"] * 0.5 +
            evaluation["completeness_score"] * 0.3 +
            (1.0 if evaluation["success"] else 0.0) * 0.2
        )
        
        # Store evaluation
        self.evaluation_history.append(evaluation)
        
        logger.debug(f"Evaluated task {task_id}: score={evaluation['overall_score']:.2f}")
        
        return evaluation
    
    def _evaluate_success(self, result: Dict[str, Any]) -> bool:
        """Determine if task was successful"""
        # Check explicit status
        if "status" in result:
            return result["status"] in ["completed", "success"]
        
        # Check for error
        if "error" in result:
            return False
        
        # Default to success if has output
        return "output" in result or "result" in result
    
    def _evaluate_quality(self, result: Dict[str, Any], task_description: str) -> float:
        """
        Evaluate result quality (0.0 to 1.0)
        
        Simple heuristic-based evaluation
        """
        score = 0.5  # Base score
        
        # Has output
        if "output" in result or "result" in result:
            score += 0.2
        
        # Has detailed result
        output = result.get("output") or result.get("result", "")
        if isinstance(output, str) and len(output) > 100:
            score += 0.1
        
        # No errors
        if "error" not in result:
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_completeness(self, result: Dict[str, Any]) -> float:
        """
        Evaluate result completeness (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Has output
        if "output" in result or "result" in result:
            score += 0.3
        
        # Has metadata
        if result.get("metadata"):
            score += 0.1
        
        # Completed status
        if result.get("status") == "completed":
            score += 0.1
        
        return min(1.0, score)
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Performance metrics
        """
        agent_evals = [
            e for e in self.evaluation_history
            if e.get("agent_id") == agent_id
        ]
        
        if not agent_evals:
            return {
                "agent_id": agent_id,
                "total_tasks": 0,
                "message": "No evaluations found"
            }
        
        total = len(agent_evals)
        successful = sum(1 for e in agent_evals if e["success"])
        avg_quality = sum(e["quality_score"] for e in agent_evals) / total
        avg_completeness = sum(e["completeness_score"] for e in agent_evals) / total
        avg_overall = sum(e["overall_score"] for e in agent_evals) / total
        
        return {
            "agent_id": agent_id,
            "total_tasks": total,
            "successful_tasks": successful,
            "success_rate": successful / total,
            "avg_quality_score": avg_quality,
            "avg_completeness_score": avg_completeness,
            "avg_overall_score": avg_overall
        }
    
    def get_task_type_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance by task type (based on description keywords)
        
        Returns:
            Performance metrics by task type
        """
        task_types = {
            "development": ["code", "build", "implement", "develop", "create", "write"],
            "devops": ["deploy", "docker", "kubernetes", "aws", "infrastructure"],
            "data": ["analyze", "data", "database", "query", "report"],
            "research": ["research", "investigate", "explore", "study"]
        }
        
        performance = {}
        
        for task_type, keywords in task_types.items():
            type_evals = [
                e for e in self.evaluation_history
                if any(kw in e.get("task_description", "").lower() for kw in keywords)
            ]
            
            if type_evals:
                total = len(type_evals)
                successful = sum(1 for e in type_evals if e["success"])
                avg_score = sum(e["overall_score"] for e in type_evals) / total
                
                performance[task_type] = {
                    "total_tasks": total,
                    "success_rate": successful / total,
                    "avg_score": avg_score
                }
        
        return performance
    
    def identify_patterns(self) -> List[Dict[str, Any]]:
        """
        Identify patterns in task outcomes
        
        Returns:
            List of identified patterns
        """
        patterns = []
        
        if len(self.evaluation_history) < 5:
            return patterns
        
        # Pattern: Consistent high performer
        agent_performance = {}
        for eval in self.evaluation_history:
            agent_id = eval.get("agent_id")
            if agent_id:
                if agent_id not in agent_performance:
                    agent_performance[agent_id] = []
                agent_performance[agent_id].append(eval["overall_score"])
        
        for agent_id, scores in agent_performance.items():
            if len(scores) >= 3 and sum(scores) / len(scores) > 0.8:
                patterns.append({
                    "type": "high_performer",
                    "agent_id": agent_id,
                    "avg_score": sum(scores) / len(scores),
                    "task_count": len(scores)
                })
        
        # Pattern: Improvement trend
        if len(self.evaluation_history) >= 10:
            recent = self.evaluation_history[-10:]
            early_avg = sum(e["overall_score"] for e in recent[:5]) / 5
            late_avg = sum(e["overall_score"] for e in recent[5:]) / 5
            
            if late_avg > early_avg + 0.1:
                patterns.append({
                    "type": "improvement_trend",
                    "early_avg": early_avg,
                    "late_avg": late_avg,
                    "improvement": late_avg - early_avg
                })
        
        return patterns
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get evaluator statistics
        
        Returns:
            Statistics dictionary
        """
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "message": "No evaluations yet"
            }
        
        total = len(self.evaluation_history)
        successful = sum(1 for e in self.evaluation_history if e["success"])
        avg_overall = sum(e["overall_score"] for e in self.evaluation_history) / total
        
        return {
            "total_evaluations": total,
            "successful_tasks": successful,
            "success_rate": successful / total,
            "avg_overall_score": avg_overall
        }
