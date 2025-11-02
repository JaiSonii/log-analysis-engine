import os
import sys
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Union

class ModelProvider:
    """
    A factory class to build and return a ChatModel instance
    based on the specified provider.
    """
    def __init__(self, provider: str, model_name: str):
        self.provider = provider.lower()
        self.model_name = model_name
        self.model : Optional[Union[ChatOpenAI, ChatGoogleGenerativeAI]] = None
        self.api_keys = {
            "openai": lambda : os.getenv('OPENAI_API_KEY', ''),
            "googleai" : lambda : os.getenv('GOOGLE_API_KEY'),
            "openrouter": lambda : os.getenv('OPENROUTER_API_KEY','')
        }
        self._validate_keys()

    def _validate_keys(self):
        """Check that the required API key for the provider is set."""
        if self.provider == "googleai" and not self.api_keys["googleai"]:
            raise ValueError("MODEL_PROVIDER is 'googleai' but GOOGLE_API_KEY is not set.")
        if self.provider == "openai" and not self.api_keys["openai"]:
            raise ValueError("MODEL_PROVIDER is 'openai' but OPENAI_API_KEY is not set.")
        if self.provider == "openrouter" and not self.api_keys["openrouter"]:
            raise ValueError("MODEL_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set.")

    def _build_openai(self) -> ChatOpenAI:
        """Builds an OpenAI model instance."""
        print(f"Building OpenAI model: {self.model_name}")
        return ChatOpenAI(
            model=self.model_name,
            temperature=0.3,
            api_key=self.api_keys["openai"]
        )
    
    def _build_googleai(self) -> ChatGoogleGenerativeAI:
        """Builds an OpenAI model instance."""
        print(f"Building OpenAI model: {self.model_name}")
        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0.3,
            google_api_key=self.api_keys["googleai"]()
        )

    def _build_openrouter(self) -> ChatOpenAI:
        """Builds an OpenRouter model instance."""
        print(f"Building OpenRouter model: {self.model_name}")
        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_keys["openrouter"],
            base_url='https://openrouter.ai/api/v1',
            temperature=0.0
        )

    def build(self) :
        """
        Public method to build the model.
        This acts as the factory.
        """
        if self.provider == "openai":
            self.model = self._build_openai()
        elif self.provider == "openrouter":
            self.model = self._build_openrouter()
        elif self.provider == 'googleai':
            self.model = self._build_googleai()
        else:
            raise ValueError(f"Unknown model provider: {self.provider}")