"""
The Learning Hub - Microsoft AutoGen Multi-Agent Conversational Framework CLI.
Demonstrates ConversableAgent two-way chat, automated code execution, and GroupChat orchestration.
"""

from __future__ import annotations
import sys
from .roadmap import AUTOGEN_STAGES, get_completed_count, get_progress_percentage
from .agent import (
    HumanInputMode,
    AssistantAgent,
    UserProxyAgent,
    ConversableAgent,
    GroupChat,
    GroupChatManager
)


def print_banner() -> None:
    print("=" * 76)
    print("   THE LEARNING HUB: AUTOGEN MULTI-AGENT CONVERSATION FRAMEWORK   ")
    print("=" * 76)


def display_roadmap() -> None:
    print("\n[+] 7-Stage AutoGen Pedagogical Mastery Roadmap:")
    for stage in AUTOGEN_STAGES:
        status = "[DONE]" if stage["completed"] else "[TODO]"
        print(f"  {status} Stage {stage['stage_number']}: {stage['title']}")
        print(f"         Focus: {stage['domain_focus']}")
    print(f"\nProgress: {get_completed_count()}/{len(AUTOGEN_STAGES)} Stages Complete ({get_progress_percentage()}%)\n")


def demonstrate_two_agent_code_execution() -> None:
    print("-" * 68)
    print("1. Two-Agent Automated Code Generation & Execution Loop")
    print("-" * 68)

    assistant = AssistantAgent(
        name="Engineer_Assistant",
        system_message="You are a senior Python engineer. Write clean code and conclude with TERMINATE when verified."
    )

    user_proxy = UserProxyAgent(
        name="User_Proxy",
        human_input_mode=HumanInputMode.NEVER,
        max_consecutive_auto_reply=4,
        code_execution_config={"work_dir": "coding", "use_docker": False}
    )

    task_prompt = "Calculate the sum of squares for integers 1 through 5 in Python."
    print(f"  [+] Initiating Chat: '{task_prompt}'\n")

    result = user_proxy.initiate_chat(recipient=assistant, message=task_prompt)

    for i, msg in enumerate(result.chat_history):
        sender = msg.get("name", "Unknown")
        content = msg.get("content", "").strip()
        print(f"  Turn {i+1} [{sender}]:")
        for line in content.split("\n"):
            print(f"    {line}")
        print()


def demonstrate_group_chat() -> None:
    print("-" * 68)
    print("2. Multi-Agent GroupChat Orchestration (Planner, Coder, Critic)")
    print("-" * 68)

    planner = ConversableAgent(
        name="Planner",
        system_message="Plans distributed architecture milestones."
    )
    # Register custom reply for planner
    planner.register_reply(
        lambda agent, msgs: (True, "Plan Milestone 1: Provision Raft cluster. Milestone 2: Wire health endpoints.")
    )

    coder = ConversableAgent(
        name="Coder",
        system_message="Implements consensus modules."
    )
    coder.register_reply(
        lambda agent, msgs: (True, "Implemented consensus heartbeat with 200ms tick interval.")
    )

    critic = ConversableAgent(
        name="Critic",
        system_message="Reviews code and architecture plans."
    )
    critic.register_reply(
        lambda agent, msgs: (True, "Security and fault tolerance checks passed. Task is complete. TERMINATE")
    )

    groupchat = GroupChat(
        agents=[planner, coder, critic],
        messages=[],
        max_round=4,
        speaker_selection_method="round_robin"
    )
    manager = GroupChatManager(groupchat=groupchat, name="group_chat_manager")

    user = ConversableAgent(name="Product_Owner")
    print("  [+] Starting GroupChat with 3 specialized agents...")
    transcript = manager.run_chat("Architect a fault-tolerant Raft consensus service.", sender=user)

    print(f"\n  [GroupChat Transcript ({len(transcript)} messages)]:")
    for entry in transcript:
        print(f"    [{entry['name']}]: {entry['content']}")
    print()


def main() -> None:
    print_banner()
    display_roadmap()
    demonstrate_two_agent_code_execution()
    demonstrate_group_chat()
    print("=" * 76)
    print("   AUTOGEN PRODUCTION FRAMEWORK DEMO COMPLETED SUCCESSFULLY   ")
    print("=" * 76)


if __name__ == "__main__":
    main()
