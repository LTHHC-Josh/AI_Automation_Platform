from src.ai.llm.llm_factory import LLMFactory


class LLMService:

    def __init__(self):

        self.provider = LLMFactory.create()

    def classify(self, text):

        return self.provider.classify(text)

    def extract(self, text, prompt):

        return self.provider.extract(text, prompt)