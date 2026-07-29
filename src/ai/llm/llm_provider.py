from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Base class for every LLM implementation.
    """

    @abstractmethod
    def classify(self, text):
        pass

    @abstractmethod
    def extract(self, text, prompt):
        pass