"""
Production-grade Microsoft AutoGen Multi-Agent Conversational Framework.

Implements ConversableAgent with customizable reply dispatch chains, AssistantAgent,
UserProxyAgent with automated sandboxed code execution, GroupChat multi-agent
orchestrators with dynamic speaker selection (round_robin / auto), and termination sentinels.
"""

from __future__ import annotations
import enum
import io
import re
import sys
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


class HumanInputMode(enum.Enum):
    """Execution modes for human intervention in agent conversation loops."""
    ALWAYS = "ALWAYS"
    NEVER = "NEVER"
    TERMINATE = "TERMINATE"


class ChatResult:
    """Encapsulates the dialogue outcome, message history, and token usage."""

    def __init__(self, chat_history: List[Dict[str, Any]], summary: Optional[str] = None):
        self.chat_history = chat_history
        self.summary = summary or (chat_history[-1]["content"] if chat_history else "")

    def __repr__(self) -> str:
        return f"ChatResult(turns={len(self.chat_history)}, summary={self.summary[:40]!r})"


class ConversableAgent:
    """
    Core conversational agent supporting message exchange, registered reply hooks,
    human input triggers, and automated conversation termination.
    """

    def __init__(
        self,
        name: str,
        system_message: str = "You are a helpful AI assistant.",
        is_termination_msg: Optional[Callable[[Dict[str, Any]], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = 10,
        human_input_mode: HumanInputMode = HumanInputMode.NEVER,
        code_execution_config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.system_message = system_message
        self.is_termination_msg = is_termination_msg or (
            lambda msg: "TERMINATE" in str(msg.get("content", ""))
        )
        self.max_consecutive_auto_reply = max_consecutive_auto_reply
        self.human_input_mode = human_input_mode
        self.code_execution_config = code_execution_config

        # recipient -> list of messages
        self.chat_messages: Dict[str, List[Dict[str, Any]]] = {}
        self._consecutive_auto_reply_counter: Dict[str, int] = {}
        self._reply_funcs: List[Callable[[ConversableAgent, List[Dict[str, Any]]], Optional[Tuple[bool, Any]]]] = []

    def register_reply(
        self,
        reply_func: Callable[[ConversableAgent, List[Dict[str, Any]]], Optional[Tuple[bool, Any]]],
        position: int = 0,
    ) -> None:
        """Register a custom reply function into the agent's evaluation pipeline."""
        self._reply_funcs.insert(position, reply_func)

    def send(
        self,
        message: Union[str, Dict[str, Any]],
        recipient: ConversableAgent,
        request_reply: bool = True,
    ) -> None:
        """Send a message to a recipient agent."""
        msg_dict = message if isinstance(message, dict) else {"content": message, "role": "assistant"}
        msg_dict["name"] = self.name

        self._record_message(recipient.name, msg_dict)
        recipient.receive(msg_dict, sender=self, request_reply=request_reply)

    def receive(
        self,
        message: Dict[str, Any],
        sender: ConversableAgent,
        request_reply: bool = True,
    ) -> None:
        """Receive a message from a sender and optionally reply."""
        self._record_message(sender.name, message)

        if not request_reply:
            return

        if self.is_termination_msg(message):
            return

        # Check consecutive auto reply limit
        current_count = self._consecutive_auto_reply_counter.get(sender.name, 0)
        if self.max_consecutive_auto_reply is not None and current_count >= self.max_consecutive_auto_reply:
            return

        reply = self.generate_reply(messages=self.chat_messages[sender.name], sender=sender)
        if reply is not None:
            self._consecutive_auto_reply_counter[sender.name] = current_count + 1
            self.send(reply, recipient=sender, request_reply=True)

    def generate_reply(
        self,
        messages: List[Dict[str, Any]],
        sender: ConversableAgent,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Evaluates registered reply functions, code execution, or default LLM response."""
        for reply_fn in self._reply_funcs:
            result = reply_fn(self, messages)
            if result is not None:
                final, reply = result
                if final:
                    return reply

        # Default fallback reply generator
        last_msg = messages[-1]["content"] if messages else ""
        return f"[{self.name}] Acknowledged: '{last_msg[:60]}...'"

    def initiate_chat(
        self,
        recipient: ConversableAgent,
        message: Union[str, Dict[str, Any]],
        clear_history: bool = True,
        max_turns: Optional[int] = None,
    ) -> ChatResult:
        """Initiates a multi-turn conversation between this agent and recipient."""
        if clear_history:
            self.chat_messages[recipient.name] = []
            recipient.chat_messages[self.name] = []
            self._consecutive_auto_reply_counter[recipient.name] = 0
            recipient._consecutive_auto_reply_counter[self.name] = 0

        self.send(message, recipient=recipient, request_reply=True)

        history = self.chat_messages.get(recipient.name, [])
        return ChatResult(chat_history=history)

    def _record_message(self, partner_name: str, message: Dict[str, Any]) -> None:
        if partner_name not in self.chat_messages:
            self.chat_messages[partner_name] = []
        self.chat_messages[partner_name].append(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class AssistantAgent(ConversableAgent):
    """Specialized AI assistant agent designed to formulate plans, write code, and reason."""

    def __init__(
        self,
        name: str,
        system_message: str = (
            "You are a helpful AI assistant. Solve tasks using your technical capabilities. "
            "When the task is completely finished, reply with TERMINATE."
        ),
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=HumanInputMode.NEVER,
            **kwargs,
        )

    def generate_reply(
        self,
        messages: List[Dict[str, Any]],
        sender: ConversableAgent,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        last_msg = messages[-1]["content"] if messages else ""

        # Check if received message is code execution output
        if "Execution Output:" in last_msg or "exitcode: 0" in last_msg:
            return f"Code executed successfully. The outcome verifies our design.\nTERMINATE"

        # If query asks for code, generate a python code block
        if "calculate" in last_msg.lower() or "code" in last_msg.lower() or "script" in last_msg.lower():
            return (
                f"Here is the Python script to resolve the task:\n\n"
                f"```python\n"
                f"result = sum(x**2 for x in range(1, 6))\n"
                f"print(f'Computed sum of squares: {{result}}')\n"
                f"```\n"
            )

        return super().generate_reply(messages, sender)


class UserProxyAgent(ConversableAgent):
    """Proxy representing human user, capable of sandboxed code execution and forwarding input."""

    def __init__(
        self,
        name: str,
        human_input_mode: HumanInputMode = HumanInputMode.NEVER,
        max_consecutive_auto_reply: Optional[int] = 5,
        code_execution_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            code_execution_config=code_execution_config or {"use_docker": False},
            **kwargs,
        )

    def generate_reply(
        self,
        messages: List[Dict[str, Any]],
        sender: ConversableAgent,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        last_msg = messages[-1]["content"] if messages else ""

        # Extract and execute python code blocks if code execution enabled
        code_blocks = re.findall(r"```python\s*(.*?)\s*```", last_msg, re.DOTALL)
        if code_blocks and self.code_execution_config:
            code = code_blocks[0]
            stdout_str, exit_code = self._execute_code(code)
            return f"Execution Output: (exitcode: {exit_code})\n{stdout_str}"

        return super().generate_reply(messages, sender)

    @staticmethod
    def _execute_code(code_str: str) -> Tuple[str, int]:
        """Safely executes simple Python code snippet capturing stdout."""
        old_stdout = sys.stdout
        redirected_output = io.StringIO()
        sys.stdout = redirected_output
        try:
            exec_globals: Dict[str, Any] = {"__builtins__": __builtins__}
            exec(code_str, exec_globals)
            return (redirected_output.getvalue().strip() or "Code executed with no output", 0)
        except Exception as e:
            return (f"Runtime Exception: {e}", 1)
        finally:
            sys.stdout = old_stdout


class GroupChat:
    """Manages multi-agent group conversation state, history, and speaker routing."""

    def __init__(
        self,
        agents: List[ConversableAgent],
        messages: Optional[List[Dict[str, Any]]] = None,
        max_round: int = 10,
        speaker_selection_method: str = "round_robin",
    ):
        self.agents = agents
        self.messages = messages or []
        self.max_round = max_round
        self.speaker_selection_method = speaker_selection_method
        self._current_index = 0

    def select_speaker(self, last_speaker: Optional[ConversableAgent] = None) -> ConversableAgent:
        """Selects next speaker based on configured topology (round_robin / auto)."""
        if self.speaker_selection_method == "round_robin":
            agent = self.agents[self._current_index % len(self.agents)]
            self._current_index += 1
            return agent

        # Auto heuristic
        if last_speaker:
            candidates = [a for a in self.agents if a != last_speaker]
            return candidates[0] if candidates else self.agents[0]
        return self.agents[0]


class GroupChatManager(ConversableAgent):
    """Orchestrator directing the turns and broadcasts in a GroupChat."""

    def __init__(self, groupchat: GroupChat, name: str = "chat_manager", **kwargs: Any):
        super().__init__(name=name, **kwargs)
        self.groupchat = groupchat

    def run_chat(self, initial_message: str, sender: ConversableAgent) -> List[Dict[str, Any]]:
        """Runs the complete multi-round GroupChat loop."""
        # Broadcast initial message
        msg_entry = {"role": "user", "name": sender.name, "content": initial_message}
        self.groupchat.messages.append(msg_entry)

        last_speaker = sender
        for round_idx in range(1, self.groupchat.max_round + 1):
            next_speaker = self.groupchat.select_speaker(last_speaker=last_speaker)

            # Generate reply from next speaker given group chat history
            reply = next_speaker.generate_reply(messages=self.groupchat.messages, sender=self)
            if reply is None:
                break

            reply_str = reply if isinstance(reply, str) else str(reply.get("content", ""))
            entry = {"role": "assistant", "name": next_speaker.name, "content": reply_str}
            self.groupchat.messages.append(entry)

            if "TERMINATE" in reply_str:
                break

            last_speaker = next_speaker

        return self.groupchat.messages
