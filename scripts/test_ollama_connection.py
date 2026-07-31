from src.ai.llm.llm_factory import LLMFactory


def main() -> None:
    print("=" * 60)
    print("Testing Local Ollama Connection")
    print("=" * 60)

    provider = LLMFactory.create()

    if not hasattr(provider, "test_connection"):
        raise RuntimeError(
            "The configured LLM provider does not support "
            "connection testing."
        )

    result = provider.test_connection()

    print(f"Server: {result['server']}")
    print(
        f"Configured model: "
        f"{result['configured_model']}"
    )
    print(
        f"Model available: "
        f"{result['model_available']}"
    )
    print("Installed models:")

    for model_name in result["installed_models"]:
        print(f"  - {model_name}")

    if not result["model_available"]:
        raise RuntimeError(
            "The configured Ollama model is not installed."
        )

    print()
    print("Ollama connection test passed.")


if __name__ == "__main__":
    main()