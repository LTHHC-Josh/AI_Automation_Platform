"""
Configuration Manager

Centralized configuration for the LTHHC AI Platform.

Every module should obtain configuration values from this file.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# ---------------------------------------------------------------------
# Project Root
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """
    Central configuration manager.
    """

    # ---------------------------------------------------------
    # Project Paths
    # ---------------------------------------------------------

    PROJECT_ROOT = PROJECT_ROOT

    CONFIG_DIR = PROJECT_ROOT / "config"
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_DIR = PROJECT_ROOT / "output"
    LOG_DIR = PROJECT_ROOT / "logs"
    PROMPT_DIR = PROJECT_ROOT / "prompts"

    # ---------------------------------------------------------
    # Smartsheet
    # ---------------------------------------------------------

    SMARTSHEET_API_TOKEN = os.getenv("SMARTSHEET_API_TOKEN")

    # ---------------------------------------------------------
    # Microsoft Graph
    # ---------------------------------------------------------

    GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID")
    GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID")
    GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET")

    # ---------------------------------------------------------
    # Ollama
    # ---------------------------------------------------------

    OLLAMA_HOST = os.getenv(
        "OLLAMA_HOST",
        "http://localhost:11434"
    )

    AI_MODEL = os.getenv(
        "AI_MODEL",
        "qwen3:8b"
    )

    # ---------------------------------------------------------
    # OCR
    # ---------------------------------------------------------

    OCR_LANGUAGE = os.getenv(
        "OCR_LANGUAGE",
        "en"
    )

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )