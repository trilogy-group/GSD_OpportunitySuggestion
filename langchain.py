from enum import Enum
import time
import os
from typing import List, Dict, Union, Type
import logging
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage


logger = logging.getLogger(__name__)


class Providers(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Speeds(str, Enum):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    SQL = "sql"


# Define provider instances mapping
PROVIDER_INSTANCES: Dict[Providers, Union[Type[ChatAnthropic], Type[ChatOpenAI]]] = {
    Providers.ANTHROPIC: ChatAnthropic,
    Providers.OPENAI: ChatOpenAI,
}

# Define speed mappings for each provider
PROVIDER_SPEEDS = {
    Providers.ANTHROPIC: {
        Speeds.SLOW: "claude-3-opus-20240229",
        Speeds.MEDIUM: "claude-3-5-sonnet-20241022",
        Speeds.FAST: "claude-3-5-haiku-20241022",
    },
    Providers.OPENAI: {
        Speeds.SLOW: "o1",
        Speeds.MEDIUM: "gpt-4o",
        Speeds.FAST: "o1-mini",
    },
    Providers.GEMINI: {
        Speeds.SLOW: "gemini-1.5-pro",
        Speeds.MEDIUM: "gemini-1.5-flash",
        Speeds.FAST: "gemini-1.5-flash-8b",
    },
}


class LangChainService:
    def __init__(self, provider: Providers = Providers.ANTHROPIC):
        self.provider = provider
        self.model: str | None = None

    def set_model(self, model: str) -> None:
        """Set the model to be used for chat completion."""
        self.model = model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_message: str,
        model_override: Speeds | None = Speeds.FAST,
    ) -> str:
        """
        Process a chat conversation and return the model's response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_message: The system message to set context
            model_override: Optional speed-based model override

        Returns:
            The model's response as a string
        """
        if model_override:
            logger.debug(
                f"Overriding model with: {PROVIDER_SPEEDS[self.provider][model_override]}"
            )
            self.set_model(PROVIDER_SPEEDS[self.provider][model_override])

        if not self.model:
            raise ValueError("Chat Model is not set!")

        is_o1_mini = self.model == "o1-mini"
        model_instance = PROVIDER_INSTANCES[self.provider](
            model=self.model,
            temperature=0.0 if is_o1_mini else 0.4,
        )

        start_time = time.time()

        # Convert messages to LangChain format
        if is_o1_mini:
            message_list = [
                HumanMessage(content=f"{system_message}\n\n{messages[0]['content']}")
            ]
        else:
            message_list = [
                SystemMessage(content=system_message),
                *[
                    AIMessage(content=msg["content"])
                    if msg["role"] == "assistant"
                    else HumanMessage(content=msg["content"])
                    for msg in messages
                ],
            ]

        invocation = await model_instance.ainvoke(message_list)

        execution_time = time.time() - start_time
        logger.debug(f"Execution took {execution_time:.2f} seconds")

        return invocation.content

    def fetch_system_prompt(self, prompt: str) -> str:
        """
        Fetch a system prompt from the prompts directory.

        Args:
            prompt: Name of the prompt file

        Returns:
            The content of the prompt file
        """
        file_path = os.path.join(
            os.getcwd(), "project/services/langchain/prompts", prompt
        )

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Default file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
