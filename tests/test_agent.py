"""
Unit test suite for the AutoGen Multi-Agent Conversational Framework.
Tests cover ConversableAgent, UserProxyAgent code execution, GroupChat orchestration, and Roadmap integrity.
"""

import unittest
from src.learn_autogen.agent import (
    HumanInputMode,
    ConversableAgent,
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager,
    ChatResult
)
from src.learn_autogen.roadmap import (
    AUTOGEN_STAGES,
    get_completed_count,
    get_progress_percentage
)


class TestAutoGenEngine(unittest.TestCase):

    def test_conversable_agent_basic_exchange(self):
        agent_a = ConversableAgent(name="AgentA", max_consecutive_auto_reply=1)
        agent_b = ConversableAgent(name="AgentB", max_consecutive_auto_reply=1)

        result = agent_a.initiate_chat(recipient=agent_b, message="Ping request")
        self.assertIsInstance(result, ChatResult)
        self.assertTrue(len(result.chat_history) >= 2)

    def test_register_reply_custom_logic(self):
        agent = ConversableAgent(name="CustomAgent")
        agent.register_reply(lambda ag, msgs: (True, "CUSTOM_REPLY_PAYLOAD"))

        sender = ConversableAgent(name="Sender")
        agent.send = lambda msg, recipient, request_reply=True: None  # mock send
        reply = agent.generate_reply(messages=[{"content": "hello"}], sender=sender)
        self.assertEqual(reply, "CUSTOM_REPLY_PAYLOAD")

    def test_user_proxy_code_execution(self):
        code = "val = 21 * 2\nprint(f'Computed {val}')"
        stdout_str, exit_code = UserProxyAgent._execute_code(code)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout_str, "Computed 42")

    def test_assistant_and_user_proxy_automated_loop(self):
        assistant = AssistantAgent(name="Assistant")
        proxy = UserProxyAgent(
            name="Proxy",
            human_input_mode=HumanInputMode.NEVER,
            max_consecutive_auto_reply=3,
            code_execution_config={"use_docker": False}
        )

        res = proxy.initiate_chat(recipient=assistant, message="Please calculate squares")
        history = res.chat_history
        self.assertTrue(len(history) >= 3)
        # Verify termination condition was triggered
        self.assertTrue(any("TERMINATE" in msg["content"] for msg in history))

    def test_group_chat_round_robin_and_termination(self):
        a1 = ConversableAgent(name="Agent1")
        a1.register_reply(lambda a, m: (True, "Agent1 message"))

        a2 = ConversableAgent(name="Agent2")
        a2.register_reply(lambda a, m: (True, "Agent2 finished task. TERMINATE"))

        group = GroupChat(
            agents=[a1, a2],
            messages=[],
            max_round=5,
            speaker_selection_method="round_robin"
        )
        manager = GroupChatManager(groupchat=group)
        user = ConversableAgent(name="User")

        transcript = manager.run_chat("Kickoff task", sender=user)
        self.assertEqual(len(transcript), 3)  # User -> Agent1 -> Agent2(TERMINATE)
        self.assertIn("TERMINATE", transcript[-1]["content"])

    def test_roadmap_7_stages(self):
        self.assertEqual(len(AUTOGEN_STAGES), 7)
        self.assertEqual(get_completed_count(), 7)
        self.assertEqual(get_progress_percentage(), 100)


if __name__ == "__main__":
    unittest.main()
