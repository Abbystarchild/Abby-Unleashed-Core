"""
Tests for the coordination system (Phase 3)
"""
import pytest
import time
from coordination.message_bus import MessageBus, Message, MessageType
from coordination.task_tracker import TaskTracker, TaskStatus
from coordination.result_aggregator import ResultAggregator


class TestMessageBus:
    """Test message bus functionality"""
    
    def test_message_creation(self):
        """Test message creation"""
        msg = Message(
            msg_type=MessageType.TASK_ASSIGNED,
            sender="test_agent",
            recipient="test_receiver",
            content={"task_id": "123"}
        )
        
        assert msg.msg_type == MessageType.TASK_ASSIGNED
        assert msg.sender == "test_agent"
        assert msg.recipient == "test_receiver"
        assert msg.content["task_id"] == "123"
        assert msg.id is not None
    
    def test_message_bus_init(self):
        """Test message bus initialization"""
        bus = MessageBus()
        assert bus.running is False
        assert bus.message_queue.qsize() == 0
        assert len(bus.subscribers) == 0
    
    def test_message_bus_start_stop(self):
        """Test message bus start and stop"""
        bus = MessageBus()
        bus.start()
        assert bus.running is True
        
        bus.stop()
        assert bus.running is False
    
    def test_publish_message(self):
        """Test publishing messages"""
        bus = MessageBus()
        bus.start()
        
        msg = Message(
            msg_type=MessageType.TASK_ASSIGNED,
            sender="test",
            content={"data": "test"}
        )
        
        bus.publish(msg)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check history
        history = bus.get_message_history()
        assert len(history) > 0
        assert history[0]["sender"] == "test"
        
        bus.stop()
    
    def test_subscribe_and_receive(self):
        """Test subscription and message delivery"""
        bus = MessageBus()
        bus.start()
        
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        # Subscribe
        bus.subscribe(MessageType.TASK_COMPLETED, callback, "test_subscriber")
        
        # Publish message
        msg = Message(
            msg_type=MessageType.TASK_COMPLETED,
            sender="agent",
            content={"result": "success"}
        )
        bus.publish(msg)
        
        # Wait for delivery
        time.sleep(0.2)
        
        # Check received
        assert len(received_messages) == 1
        assert received_messages[0].content["result"] == "success"
        
        bus.stop()
    
    def test_message_filtering(self):
        """Test message type filtering"""
        bus = MessageBus()
        bus.start()
        
        received_task_assigned = []
        received_task_completed = []
        
        def callback_assigned(msg):
            received_task_assigned.append(msg)
        
        def callback_completed(msg):
            received_task_completed.append(msg)
        
        # Subscribe to different types
        bus.subscribe(MessageType.TASK_ASSIGNED, callback_assigned, "sub1")
        bus.subscribe(MessageType.TASK_COMPLETED, callback_completed, "sub2")
        
        # Publish different messages
        bus.publish(Message(MessageType.TASK_ASSIGNED, "agent1"))
        bus.publish(Message(MessageType.TASK_COMPLETED, "agent2"))
        bus.publish(Message(MessageType.TASK_ASSIGNED, "agent3"))
        
        time.sleep(0.2)
        
        # Check filtering
        assert len(received_task_assigned) == 2
        assert len(received_task_completed) == 1
        
        bus.stop()


class TestTaskTracker:
    """Test task tracker functionality"""
    
    def test_task_tracker_init(self):
        """Test task tracker initialization"""
        tracker = TaskTracker()
        assert len(tracker.tasks) == 0
    
    def test_add_task(self):
        """Test adding tasks"""
        tracker = TaskTracker()
        
        task = tracker.add_task(
            task_id="task1",
            description="Test task",
            dependencies=["task0"]
        )
        
        assert task.task_id == "task1"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert "task0" in task.dependencies
    
    def test_task_lifecycle(self):
        """Test complete task lifecycle"""
        tracker = TaskTracker()
        
        # Add task
        task = tracker.add_task("task1", "Test task")
        assert task.status == TaskStatus.PENDING
        
        # Assign
        tracker.assign_task("task1", "agent1")
        assert task.status == TaskStatus.ASSIGNED
        assert task.agent_id == "agent1"
        
        # Start
        tracker.start_task("task1", "agent1")
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        
        # Update progress
        tracker.update_progress("task1", 0.5)
        assert task.progress == 0.5
        
        # Complete
        tracker.complete_task("task1", {"output": "result"})
        assert task.status == TaskStatus.COMPLETED
        assert task.result["output"] == "result"
        assert task.completed_at is not None
    
    def test_task_failure(self):
        """Test task failure"""
        tracker = TaskTracker()
        
        task = tracker.add_task("task1", "Test task")
        tracker.start_task("task1", "agent1")
        tracker.fail_task("task1", "Error occurred")
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Error occurred"
    
    def test_get_ready_tasks(self):
        """Test getting ready tasks"""
        tracker = TaskTracker()
        
        # Add tasks with dependencies
        tracker.add_task("task1", "Task 1")
        tracker.add_task("task2", "Task 2", dependencies=["task1"])
        tracker.add_task("task3", "Task 3")
        
        # Initially, task1 and task3 are ready
        ready = tracker.get_ready_tasks()
        assert len(ready) == 2
        assert any(t.task_id == "task1" for t in ready)
        assert any(t.task_id == "task3" for t in ready)
        
        # Complete task1
        tracker.complete_task("task1", {})
        
        # Now task2 should be ready
        ready = tracker.get_ready_tasks()
        assert any(t.task_id == "task2" for t in ready)
    
    def test_get_tasks_by_status(self):
        """Test filtering tasks by status"""
        tracker = TaskTracker()
        
        tracker.add_task("task1", "Task 1")
        tracker.add_task("task2", "Task 2")
        tracker.start_task("task1", "agent1")
        
        pending = tracker.get_tasks_by_status(TaskStatus.PENDING)
        in_progress = tracker.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        
        assert len(pending) == 1
        assert len(in_progress) == 1
        assert pending[0].task_id == "task2"
        assert in_progress[0].task_id == "task1"
    
    def test_overall_progress(self):
        """Test overall progress calculation"""
        tracker = TaskTracker()
        
        tracker.add_task("task1", "Task 1")
        tracker.add_task("task2", "Task 2")
        
        assert tracker.get_overall_progress() == 0.0
        
        tracker.complete_task("task1", {})
        assert tracker.get_overall_progress() == 0.5
        
        tracker.complete_task("task2", {})
        assert tracker.get_overall_progress() == 1.0


class TestResultAggregator:
    """Test result aggregator functionality"""
    
    def test_result_aggregator_init(self):
        """Test result aggregator initialization"""
        agg = ResultAggregator()
        assert len(agg.results) == 0
    
    def test_add_result(self):
        """Test adding results"""
        agg = ResultAggregator()
        
        result_id = agg.add_result(
            task_id="task1",
            agent_id="agent1",
            output="test output",
            metadata={"key": "value"}
        )
        
        assert result_id is not None
        result = agg.get_result(result_id)
        assert result.task_id == "task1"
        assert result.agent_id == "agent1"
        assert result.output == "test output"
    
    def test_get_task_results(self):
        """Test getting results for a task"""
        agg = ResultAggregator()
        
        agg.add_result("task1", "agent1", "output1")
        agg.add_result("task1", "agent2", "output2")
        agg.add_result("task2", "agent1", "output3")
        
        task1_results = agg.get_task_results("task1")
        assert len(task1_results) == 2
        
        task2_results = agg.get_task_results("task2")
        assert len(task2_results) == 1
    
    def test_aggregate_task_results(self):
        """Test aggregating task results"""
        agg = ResultAggregator()
        
        agg.add_result("task1", "agent1", "result1")
        agg.add_result("task1", "agent2", "result2")
        
        aggregated = agg.aggregate_task_results("task1")
        
        assert aggregated["task_id"] == "task1"
        assert aggregated["status"] == "completed"
        assert aggregated["num_results"] == 2
        assert len(aggregated["agents"]) == 2
    
    def test_aggregate_workflow_results(self):
        """Test aggregating workflow results"""
        agg = ResultAggregator()
        
        agg.add_result("task1", "agent1", "result1")
        agg.add_result("task2", "agent2", "result2")
        
        workflow = agg.aggregate_workflow_results(["task1", "task2"])
        
        assert workflow["workflow"]["total_tasks"] == 2
        assert workflow["workflow"]["total_results"] == 2
        assert len(workflow["task_results"]) == 2
    
    def test_format_output(self):
        """Test output formatting"""
        agg = ResultAggregator()
        
        agg.add_result("task1", "agent1", "result1")
        
        summary = agg.format_final_output(["task1"], format_type="summary")
        assert "Workflow completed" in summary
        
        detailed = agg.format_final_output(["task1"], format_type="detailed")
        assert "WORKFLOW RESULTS" in detailed
        
        json_output = agg.format_final_output(["task1"], format_type="json")
        assert "{" in json_output


class TestCoordinationIntegration:
    """Integration tests for coordination system"""
    
    def test_full_workflow(self):
        """Test complete coordination workflow"""
        # Initialize components
        bus = MessageBus()
        tracker = TaskTracker()
        aggregator = ResultAggregator()
        
        bus.start()
        
        # Track messages
        messages_received = []
        
        def message_callback(msg):
            messages_received.append(msg)
        
        bus.subscribe(MessageType.TASK_ASSIGNED, message_callback, "test")
        bus.subscribe(MessageType.TASK_COMPLETED, message_callback, "test")
        
        # Add tasks
        task1 = tracker.add_task("task1", "First task")
        task2 = tracker.add_task("task2", "Second task", dependencies=["task1"])
        
        # Execute task1
        bus.publish(Message(MessageType.TASK_ASSIGNED, "orchestrator", content={"task_id": "task1"}))
        tracker.start_task("task1", "agent1")
        tracker.complete_task("task1", {"output": "result1"})
        aggregator.add_result("task1", "agent1", "result1")
        bus.publish(Message(MessageType.TASK_COMPLETED, "agent1", content={"task_id": "task1"}))
        
        time.sleep(0.2)
        
        # Check task2 is now ready
        ready_tasks = tracker.get_ready_tasks()
        assert any(t.task_id == "task2" for t in ready_tasks)
        
        # Execute task2
        tracker.start_task("task2", "agent2")
        tracker.complete_task("task2", {"output": "result2"})
        aggregator.add_result("task2", "agent2", "result2")
        
        # Verify workflow
        workflow = aggregator.aggregate_workflow_results(["task1", "task2"])
        assert workflow["workflow"]["total_tasks"] == 2
        assert workflow["workflow"]["total_results"] == 2
        
        # Verify messages
        assert len(messages_received) >= 2
        
        bus.stop()
