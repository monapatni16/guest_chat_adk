from typing import Callable
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner

def reverse_text(text: str) -> dict:
    return {"status": "ok", "result": text[::-1]}

def build_agent():
    # Create a simple function tool
    reverse_tool = FunctionTool(
      #  name="reverse_text",
        func=reverse_text,
     #   description="Reverses input text",
    )

    root_agent = LlmAgent(
        name="guest_chat_agent",
        model="gemini-1.5-flash",
        description="Demo agent for guest chat",
        instruction="You are a helpful assistant for a web chat. Keep responses concise.",
        tools=[reverse_tool],
    )

    # InMemoryRunner provides a runner and an in-memory session service
    runner = InMemoryRunner(app_name="guest_chat_app", agent=root_agent)
    session_service = runner.session_service

    return root_agent, runner, session_service
