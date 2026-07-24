# LTHHC AI Platform Architecture

## Project Vision

The LTHHC AI Platform is the centralized automation and artificial intelligence platform for LT Home Healthcare.

The platform is designed to automate business processes, process documents, integrate with company systems, and provide a foundation for future AI initiatives.

---

# Core Design Principles

- Python is the central orchestration engine.
- All AI processing runs locally using Ollama.
- No cloud AI services are required.
- Every module is designed to be reusable.
- Business logic resides only within the Python application.
- The platform is modular, maintainable, and scalable.

---

# Current Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| AI Runtime | Ollama |
| Initial AI Model | Qwen3 8B Instruct |
| OCR | PaddleOCR |
| Mail Integration | Microsoft Graph API |
| Project Management | Smartsheet API |
| Operating System | Windows 11 Pro |

---

# Current Project Structure

```
LTHHC-AI/
│
├── config/
├── data/
├── docs/
├── logs/
├── output/
├── prompts/
├── scripts/
│
└── src/
    ├── ai/
    ├── business_rules/
    ├── core/
    ├── graph/
    ├── ocr/
    ├── smartsheet/
    ├── utils/
```

---

# Core Components

## Config

Centralized configuration management.

Responsible for:

- Environment variables
- Directory paths
- API configuration
- AI configuration

---

## Logger

Centralized logging for every platform component.

Responsible for:

- Console logging
- File logging
- Error reporting
- Audit support

---

## Application

Main application bootstrap.

Eventually responsible for initializing:

- Configuration
- Logging
- Microsoft Graph
- OCR
- AI
- Smartsheet
- Workflow Engine

---

# Planned Processing Workflow

Microsoft 365 Outlook

↓

Microsoft Graph API

↓

Attachment Processing

↓

OCR (PaddleOCR)

↓

AI Processing (Ollama)

↓

Business Rules

↓

Smartsheet

↓

Reporting / Logging

↓

Archive / Manual Review

---

# Development Status

## Completed

- Project structure
- Smartsheet connectivity
- Task browsing
- Status updates
- Central configuration
- Central logging
- Application bootstrap

## Next

- Migrate Smartsheet code into new architecture
- Build Ollama AI service
- Build Microsoft Graph service
- Build OCR service
- Build workflow engine

---

Last Updated

July 24, 2026