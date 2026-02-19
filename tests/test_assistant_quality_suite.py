import pytest
import os
from unittest.mock import Mock

from streaming_conversation import StreamingConversation
from copilot_bridge import CopilotBridge
from speech_interface import ConversationManager
from agents.base_agent import Agent, AgentDNA


class FakeBrainClone:
    def get_personality(self):
        return {
            "identity": {"name": "Abby"},
            "communication_style": {"tone": "direct"}
        }


class FakeOllamaClient:
    def __init__(self):
        self.calls = []

    def chat(self, messages, model, stream=False):
        self.calls.append({
            "messages": messages,
            "model": model,
            "stream": stream,
        })
        if stream:
            return iter([
                {"message": {"content": "OK"}},
                {"done": True}
            ])
        return {"message": {"content": "OK"}, "done": True}


class FakeAbby:
    def __init__(self, ollama_client=None):
        self.brain_clone = FakeBrainClone()
        self.ollama_client = ollama_client or FakeOllamaClient()
        self.model_selector = Mock()
        self.model_selector.select_model.return_value = "qwen2.5-coder:latest"

    def execute_task(self, text):
        return {"output": f"Processed: {text}"}


def collect_events(conversation, user_input, context=None):
    return list(conversation.stream_response(user_input, context or {}))


def test_streaming_includes_user_prompt_addition():
    client = FakeOllamaClient()
    abby = FakeAbby(ollama_client=client)
    sc = StreamingConversation(abby)

    collect_events(sc, "Hello", {"user_prompt_addition": "SYSTEM NOTE"})

    assert client.calls, "Expected Ollama chat call"
    system_prompt = client.calls[0]["messages"][0]["content"]
    assert "SYSTEM NOTE" in system_prompt


def test_streaming_includes_system_note_for_three_way_chat():
    client = FakeOllamaClient()
    abby = FakeAbby(ollama_client=client)
    sc = StreamingConversation(abby)

    collect_events(sc, "Hello", {"system_note": "You are in a three-way conversation"})

    system_prompt = client.calls[0]["messages"][0]["content"]
    assert "three-way conversation" in system_prompt


def test_streaming_uses_model_selector_for_code_tasks():
    client = FakeOllamaClient()
    abby = FakeAbby(ollama_client=client)
    sc = StreamingConversation(abby)

    collect_events(sc, "Write Kotlin code to parse JSON", {})

    # Expect streaming to use model_selector for code tasks
    assert client.calls, "Expected Ollama chat call"
    assert client.calls[0]["model"] == "qwen2.5-coder:latest"


def test_enable_personaplex_fallback_without_elevenlabs(monkeypatch):
    # Ensure no ElevenLabs credentials are set
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)

    abby = FakeAbby()
    sc = StreamingConversation(abby)

    # Patch ConversationManager to inspect tts_backend argument
    called = {}

    def fake_init(self, *args, **kwargs):
        called["tts_backend"] = kwargs.get("tts_backend")

    monkeypatch.setattr(ConversationManager, "__init__", fake_init, raising=False)
    monkeypatch.setattr(ConversationManager, "set_task_executor", lambda *args, **kwargs: None, raising=False)
    monkeypatch.setattr(ConversationManager, "initialize", lambda *args, **kwargs: True, raising=False)

    ok = sc.enable_personaplex()
    assert ok is True
    assert called.get("tts_backend") in (None, "piper")


def test_copilot_bridge_request_flow(tmp_path):
    bridge = CopilotBridge(storage_path=str(tmp_path))

    req = bridge.request_from_copilot("analyze file", {"path": "foo.py"})
    pending = bridge.get_pending_requests(for_sender="abby")

    assert len(pending) == 1
    assert pending[0]["id"] == req.id

    response = bridge.respond_to_request(req.id, "done", "abby")
    assert response.type == "response"

    pending_after = bridge.get_pending_requests(for_sender="abby")
    assert len(pending_after) == 0


def test_copilot_bridge_context_roundtrip(tmp_path):
    bridge = CopilotBridge(storage_path=str(tmp_path))

    bridge.set_context("key1", {"a": 1}, sender="abby")
    assert bridge.get_context("key1") == {"a": 1}

    bridge.clear_context()
    assert bridge.get_context("key1") is None


def test_agent_research_trigger_for_latest_keywords():
    dna = AgentDNA(
        role="Researcher",
        seniority="Senior",
        domain="AI",
        industry_knowledge=["LLMs"],
        methodologies=["Research"],
        constraints={"quality": "high"},
        output_format={"report": "summary"},
    )
    agent = Agent(dna=dna)

    assert agent._should_research_task("What are the latest LLM benchmarks?") is True
    assert agent._should_research_task("Explain transformers") is True

