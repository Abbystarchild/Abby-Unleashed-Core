"""
Delegation optimizer for improving agent selection and task routing
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DelegationOptimizer:
    """
    Optimizes agent delegation decisions
    
    Learns from past performance to improve future agent selection
    """
    
    def __init__(self):
        """Initialize delegation optimizer"""
        self.delegation_history: List[Dict[str, Any]] = []
        self.agent_specialties: Dict[str, Dict[str, float]] = {}
        logger.info("Delegation optimizer initialized")
    
    def record_delegation(
        self,
        task_id: str,
        task_description: str,
        agent_id: str,
        task_type: str,
        outcome_score: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a delegation decision and its outcome
        
        Args:
            task_id: Task identifier
            task_description: Task description
            agent_id: Selected agent
            task_type: Type of task
            outcome_score: Outcome score (0.0 to 1.0)
            metadata: Optional metadata
        """
        record = {
            "task_id": task_id,
            "task_description": task_description,
            "agent_id": agent_id,
            "task_type": task_type,
            "outcome_score": outcome_score,
            "metadata": metadata or {},
            "recorded_at": datetime.now().isoformat()
        }
        
        self.delegation_history.append(record)
        
        # Update agent specialties
        self._update_agent_specialties(agent_id, task_type, outcome_score)
        
        logger.debug(f"Recorded delegation: {agent_id} -> {task_type}")
    
    def _update_agent_specialties(self, agent_id: str, task_type: str, score: float):
        """Update agent specialty scores"""
        if agent_id not in self.agent_specialties:
            self.agent_specialties[agent_id] = {}
        
        # Update with exponential moving average
        current = self.agent_specialties[agent_id].get(task_type, 0.5)
        alpha = 0.3  # Learning rate
        new_score = alpha * score + (1 - alpha) * current
        
        self.agent_specialties[agent_id][task_type] = new_score
    
    def recommend_agent(
        self,
        task_type: str,
        available_agents: List[str]
    ) -> Optional[str]:
        """
        Recommend best agent for task type
        
        Args:
            task_type: Type of task
            available_agents: List of available agent IDs
            
        Returns:
            Recommended agent ID or None
        """
        if not available_agents:
            return None
        
        # Score each agent for this task type
        agent_scores = {}
        
        for agent_id in available_agents:
            if agent_id in self.agent_specialties:
                score = self.agent_specialties[agent_id].get(task_type, 0.5)
                agent_scores[agent_id] = score
            else:
                # New agent, default score
                agent_scores[agent_id] = 0.5
        
        # Return agent with highest score
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            logger.debug(f"Recommended {best_agent[0]} for {task_type} (score: {best_agent[1]:.2f})")
            return best_agent[0]
        
        return available_agents[0]  # Default to first
    
    def get_agent_specialties(self, agent_id: str) -> Dict[str, float]:
        """
        Get agent's specialty scores
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary of task types to scores
        """
        return self.agent_specialties.get(agent_id, {})
    
    def get_top_performers(
        self,
        task_type: str,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get top performing agents for task type
        
        Args:
            task_type: Task type
            top_n: Number of top performers to return
            
        Returns:
            List of agent performance dictionaries
        """
        performers = []
        
        for agent_id, specialties in self.agent_specialties.items():
            if task_type in specialties:
                performers.append({
                    "agent_id": agent_id,
                    "score": specialties[task_type]
                })
        
        # Sort by score
        performers.sort(key=lambda x: x["score"], reverse=True)
        
        return performers[:top_n]
    
    def analyze_delegation_patterns(self) -> Dict[str, Any]:
        """
        Analyze delegation patterns and efficiency
        
        Returns:
            Analysis dictionary
        """
        if not self.delegation_history:
            return {"message": "No delegation history"}
        
        # Calculate overall metrics
        total = len(self.delegation_history)
        avg_score = sum(d["outcome_score"] for d in self.delegation_history) / total
        
        # Task type distribution
        task_types = {}
        for delegation in self.delegation_history:
            task_type = delegation["task_type"]
            task_types[task_type] = task_types.get(task_type, 0) + 1
        
        # Agent workload
        agent_workload = {}
        for delegation in self.delegation_history:
            agent_id = delegation["agent_id"]
            agent_workload[agent_id] = agent_workload.get(agent_id, 0) + 1
        
        # Identify best pairings (agent + task type)
        pairings = {}
        for delegation in self.delegation_history:
            key = f"{delegation['agent_id']}:{delegation['task_type']}"
            if key not in pairings:
                pairings[key] = []
            pairings[key].append(delegation["outcome_score"])
        
        best_pairings = []
        for key, scores in pairings.items():
            if len(scores) >= 2:  # At least 2 examples
                agent_id, task_type = key.split(":", 1)
                avg = sum(scores) / len(scores)
                if avg > 0.7:  # Good performance
                    best_pairings.append({
                        "agent_id": agent_id,
                        "task_type": task_type,
                        "avg_score": avg,
                        "count": len(scores)
                    })
        
        best_pairings.sort(key=lambda x: x["avg_score"], reverse=True)
        
        return {
            "total_delegations": total,
            "avg_outcome_score": avg_score,
            "task_type_distribution": task_types,
            "agent_workload": agent_workload,
            "best_pairings": best_pairings[:10]
        }
    
    def generate_optimization_suggestions(self) -> List[str]:
        """
        Generate suggestions for improving delegation
        
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        if len(self.delegation_history) < 5:
            return ["Need more delegation data (at least 5 examples)"]
        
        analysis = self.analyze_delegation_patterns()
        
        # Check for workload imbalance
        workload = analysis.get("agent_workload", {})
        if workload:
            max_load = max(workload.values())
            min_load = min(workload.values())
            if max_load > min_load * 3:
                suggestions.append(
                    f"Consider load balancing: Some agents handle {max_load} tasks "
                    f"while others handle only {min_load}"
                )
        
        # Check for low-performing task types
        for agent_id, specialties in self.agent_specialties.items():
            low_performing = [
                task_type for task_type, score in specialties.items()
                if score < 0.4
            ]
            if low_performing:
                suggestions.append(
                    f"Agent {agent_id} struggles with: {', '.join(low_performing)}. "
                    "Consider reassigning or additional training."
                )
        
        # Recommend specialist utilization
        best_pairings = analysis.get("best_pairings", [])
        if best_pairings:
            top = best_pairings[0]
            suggestions.append(
                f"Excellent pairing found: {top['agent_id']} excels at "
                f"{top['task_type']} (avg score: {top['avg_score']:.2f}). "
                "Prioritize this pairing."
            )
        
        return suggestions if suggestions else ["Delegation is performing well!"]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get optimizer statistics
        
        Returns:
            Statistics dictionary
        """
        return {
            "total_delegations": len(self.delegation_history),
            "known_agents": len(self.agent_specialties),
            "total_specialties": sum(len(s) for s in self.agent_specialties.values())
        }
