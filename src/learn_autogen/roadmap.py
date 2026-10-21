"""
The Learning Hub - AutoGen Pedagogical Mastery Roadmap.
7-Stage progression covering ConversableAgent, GroupChat, Sandboxed Code Execution, and Actor Model.
"""

from typing import List, Dict, Any

AUTOGEN_STAGES: List[Dict[str, Any]] = [
    {
        "stage_number": 1,
        "title": "AutoGen Architecture Evolution & Core Foundations",
        "domain_focus": "ConversableAgent abstractions, reply functions, termination conditions, and system messages.",
        "completed": True,
        "key_topics": ["ConversableAgent Lifecycle", "register_reply Mechanisms", "Termination Sentinels", "LLM Config & Cache"]
    },
    {
        "stage_number": 2,
        "title": "Multi-Agent Conversations, GroupChat & Dynamic Orchestration",
        "domain_focus": "GroupChat topologies, GroupChatManager, speaker selection (auto, round_robin, constrained graphs).",
        "completed": True,
        "key_topics": ["GroupChat Topology", "Speaker Selection Strategy", "Constrained Conversation Graphs", "Manager Broadcast Protocol"]
    },
    {
        "stage_number": 3,
        "title": "Code Execution, Sandboxing & Tool Use",
        "domain_focus": "UserProxyAgent code execution, Docker/Dockerless sandboxing, safe evaluation, and function registration.",
        "completed": True,
        "key_topics": ["CodeExecutionConfig", "LocalCommandLineCodeExecutor", "Docker Sandboxing", "Function Calling Tools"]
    },
    {
        "stage_number": 4,
        "title": "Advanced Patterns: Human-in-the-Loop, Teachability & Memory",
        "domain_focus": "Human input modes (ALWAYS, NEVER, TERMINATE), Teachability module, and long-term vector memory.",
        "completed": True,
        "key_topics": ["HumanInputMode Options", "Teachability & Fact Recall", "ChromaDB Session Memory", "Agent State Snapshots"]
    },
    {
        "stage_number": 5,
        "title": "AutoGen 0.4+ Modern Event-Driven AgentChat & Actor Model",
        "domain_focus": "gRPC/WebSocket actor model, asynchronous message passing, AgentContext, and event loops.",
        "completed": True,
        "key_topics": ["AutoGen 0.4+ Actor Architecture", "Async Agent Protocols", "Distributed Agent Addressing", "Event Message Bus"]
    },
    {
        "stage_number": 6,
        "title": "Production Engineering, Webhooks, FastAPI & Observability",
        "domain_focus": "FastAPI asynchronous webhooks, distributed agent sessions, OpenTelemetry, and token budgeting.",
        "completed": True,
        "key_topics": ["FastAPI SSE Streaming", "Agent Session Isolation", "OpenTelemetry Tracing", "Cost & Latency Budgets"]
    },
    {
        "stage_number": 7,
        "title": "Production API Reference & 50 Staff-Level Interview Questions",
        "domain_focus": "Staff architecture trade-offs, multi-agent deadlocks, consensus loops, and enterprise hardening.",
        "completed": True,
        "key_topics": ["Deadlock Prevention", "Cascading Token Failures", "Sandboxing Security Boundaries", "Production Cheatsheet"]
    }
]

def get_completed_count() -> int:
    return sum(1 for s in AUTOGEN_STAGES if s["completed"])

def get_progress_percentage() -> int:
    return round((get_completed_count() / len(AUTOGEN_STAGES)) * 100)
