"""
Plan Management API Routes for Abby Unleashed

Provides REST API for:
- Viewing plans and queue
- Editing plans and tasks
- Managing plan status (pause, resume, archive, delete)
- Adding context to tasks
"""

from flask import Blueprint, request, jsonify
import logging

from plan_manager import get_plan_manager

logger = logging.getLogger(__name__)

plan_routes = Blueprint('plans', __name__, url_prefix='/api/plans')


@plan_routes.route('/', methods=['GET'])
def get_all_plans():
    """Get all plans"""
    try:
        manager = get_plan_manager()
        plans = manager.get_all_plans()
        return jsonify({"plans": plans})
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/queue', methods=['GET'])
def get_queue():
    """Get the active queue"""
    try:
        manager = get_plan_manager()
        queue = manager.get_queue()
        return jsonify({"queue": queue})
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get a specific plan"""
    try:
        manager = get_plan_manager()
        plan = manager.get_plan(plan_id)
        
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Include metadata
        meta = manager.metadata.get(plan_id)
        if meta:
            plan["_metadata"] = {
                "status": meta.status,
                "priority": meta.priority,
                "user_notes": meta.user_notes,
                "tags": meta.tags,
            }
        
        return jsonify(plan)
    except Exception as e:
        logger.error(f"Error getting plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>', methods=['PUT'])
def update_plan(plan_id):
    """Update a plan"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get existing plan
        plan = manager.get_plan(plan_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Update allowed fields
        if "summary" in data:
            plan["summary"] = data["summary"]
        if "original_request" in data:
            plan["original_request"] = data["original_request"]
        if "tasks" in data:
            plan["tasks"] = data["tasks"]
        
        # Save
        success = manager.save_plan(plan_id, plan)
        
        if success:
            return jsonify({"message": "Plan updated", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to save plan"}), 500
    except Exception as e:
        logger.error(f"Error updating plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    """Delete a plan"""
    try:
        manager = get_plan_manager()
        success = manager.delete_plan(plan_id)
        
        if success:
            return jsonify({"message": "Plan deleted", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to delete plan"}), 500
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/status', methods=['PUT'])
def update_status(plan_id):
    """Update plan status (queued, paused, archived, etc.)"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        status = data.get("status")
        if not status:
            return jsonify({"error": "No status provided"}), 400
        
        success = manager.set_status(plan_id, status)
        
        if success:
            return jsonify({"message": f"Plan status set to {status}", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to update status"}), 500
    except Exception as e:
        logger.error(f"Error updating status for {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/priority', methods=['PUT'])
def update_priority(plan_id):
    """Update plan priority"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        priority = data.get("priority")
        if priority is None:
            return jsonify({"error": "No priority provided"}), 400
        
        success = manager.set_priority(plan_id, int(priority))
        
        if success:
            return jsonify({"message": f"Plan priority set to {priority}", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to update priority"}), 500
    except Exception as e:
        logger.error(f"Error updating priority for {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/notes', methods=['PUT'])
def update_notes(plan_id):
    """Update user notes on a plan"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        notes = data.get("notes", "")
        success = manager.update_plan_notes(plan_id, notes)
        
        if success:
            return jsonify({"message": "Notes updated", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to update notes"}), 500
    except Exception as e:
        logger.error(f"Error updating notes for {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/tasks/<task_id>', methods=['PUT'])
def update_task(plan_id, task_id):
    """Update a specific task"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = manager.update_task(plan_id, task_id, data)
        
        if success:
            return jsonify({"message": "Task updated", "plan_id": plan_id, "task_id": task_id})
        else:
            return jsonify({"error": "Failed to update task"}), 500
    except Exception as e:
        logger.error(f"Error updating task {task_id} in {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/tasks/<task_id>/context', methods=['POST'])
def add_task_context(plan_id, task_id):
    """Add context to a specific task"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        context = data.get("context", "")
        if not context:
            return jsonify({"error": "No context provided"}), 400
        
        success = manager.add_task_context(plan_id, task_id, context)
        
        if success:
            return jsonify({"message": "Context added", "plan_id": plan_id, "task_id": task_id})
        else:
            return jsonify({"error": "Failed to add context"}), 500
    except Exception as e:
        logger.error(f"Error adding context to task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/tasks', methods=['POST'])
def add_task(plan_id):
    """Add a new task to a plan"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        if not data or "title" not in data:
            return jsonify({"error": "Task title required"}), 400
        
        success = manager.add_task_to_plan(plan_id, data)
        
        if success:
            return jsonify({"message": "Task added", "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to add task"}), 500
    except Exception as e:
        logger.error(f"Error adding task to {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/tasks/<task_id>', methods=['DELETE'])
def remove_task(plan_id, task_id):
    """Remove a task from a plan"""
    try:
        manager = get_plan_manager()
        success = manager.remove_task_from_plan(plan_id, task_id)
        
        if success:
            return jsonify({"message": "Task removed", "plan_id": plan_id, "task_id": task_id})
        else:
            return jsonify({"error": "Failed to remove task"}), 500
    except Exception as e:
        logger.error(f"Error removing task {task_id} from {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/<plan_id>/split', methods=['POST'])
def split_plan(plan_id):
    """Split a plan into two at a specific task"""
    try:
        manager = get_plan_manager()
        data = request.get_json()
        
        split_at = data.get("split_at_task")
        if not split_at:
            return jsonify({"error": "split_at_task required"}), 400
        
        new_plan_id = manager.split_plan(plan_id, split_at)
        
        if new_plan_id:
            return jsonify({
                "message": "Plan split successfully",
                "original_plan_id": plan_id,
                "new_plan_id": new_plan_id
            })
        else:
            return jsonify({"error": "Failed to split plan"}), 500
    except Exception as e:
        logger.error(f"Error splitting plan {plan_id}: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/active', methods=['GET'])
def get_active():
    """Get the currently active plan"""
    try:
        manager = get_plan_manager()
        plan = manager.get_active_plan()
        
        if plan:
            return jsonify(plan)
        else:
            return jsonify({"message": "No active plan"})
    except Exception as e:
        logger.error(f"Error getting active plan: {e}")
        return jsonify({"error": str(e)}), 500


@plan_routes.route('/next-task', methods=['GET'])
def get_next_task():
    """Get the next task to work on"""
    try:
        manager = get_plan_manager()
        task_info = manager.get_next_task()
        
        if task_info:
            return jsonify(task_info)
        else:
            return jsonify({"message": "No pending tasks"})
    except Exception as e:
        logger.error(f"Error getting next task: {e}")
        return jsonify({"error": str(e)}), 500
