# Kisan Mitra AI - Folder Structure Specification

This document details the directory structure of the **Kisan Mitra AI** repository, explaining the purpose of each directory and its components.

---

## Complete Tree Structure

```
kisan-mitra-ai/
├── .github/                # GitHub-specific files
│   ├── ISSUE_TEMPLATE/     # Templates for bug reports and features
│   ├── workflows/          # CI/CD pipelines and checks
│   ├── CODEOWNERS          # Source code ownership file
│   └── PULL_REQUEST_TEMPLATE.md
├── backend/                # FastAPI Application & AI Agents
│   ├── app/                # Main application code
│   │   ├── api/            # API endpoints & route handlers
│   │   ├── config/         # Environment specific configurations
│   │   ├── core/           # Security, configuration, and logging setup
│   │   ├── database/       # DB connections, sessions, and migrations
│   │   ├── dependencies/   # FastAPI Dependency Injection definitions
│   │   ├── middleware/     # Custom middlewares (CORS, requests loggers)
│   │   ├── models/         # Database models (SQLAlchemy / SQLModel)
│   │   ├── orchestrator/   # Agent Graph routers & LangGraph setups
│   │   ├── prompts/        # Centralized LLM system prompts
│   │   ├── schemas/        # Request/response validation schemas (Pydantic)
│   │   ├── services/       # Core business logic/use cases
│   │   └── utils/          # General helper functions
│   ├── agents/             # Multi-agent implementations
│   │   ├── base/           # Abstract classes for agents
│   │   ├── planner/        # Intent classification & routing
│   │   ├── market/         # Commodity prices and trends
│   │   ├── weather/        # Meteorological advisory
│   │   ├── disease/        # Crop pathology and diagnosis
│   │   ├── schemes/        # Government program searches
│   │   ├── finance/        # Micro-loans and banking advisory
│   │   ├── irrigation/     # Water schedules and soil moisture
│   │   ├── soil/           # Soil chemistry & nutrient advisors
│   │   ├── translation/    # Localization/Vernacular translation
│   │   ├── memory/         # History & profile state
│   │   └── verifier/       # Output verification & sanitization
│   ├── tests/              # Unit & integration tests
│   ├── requirements.txt    # Production python packages
│   └── pyproject.toml      # Ruff, Black, isort, mypy configuration
├── frontend/               # Next.js Application
│   ├── app/                # Next.js pages and routes (App Router)
│   ├── components/         # Reusable UI component library (shadcn/ui)
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Shared clients (e.g. axios wrapper, utils)
│   ├── public/             # Static icons, logos, fonts
│   ├── services/           # Backend API clients
│   ├── styles/             # Global Tailwind/CSS rules
│   ├── tsconfig.json       # TypeScript configuration
│   ├── tailwind.config.ts  # Tailwind configuration
│   ├── postcss.config.mjs  # Postcss configuration
│   └── components.json     # shadcn/ui configuration
├── knowledge/              # Knowledge bases for Retrieval-Augmented Generation (RAG)
│   ├── crops/              # Crop cycle guides
│   ├── diseases/           # Symptom catalogs
│   ├── fertilizers/        # N-P-K recommendation guides
│   ├── pesticides/         # Pest advisory guides
│   ├── government_schemes/  # Schemes metadata
│   ├── market/             # Market pricing guidelines
│   ├── weather/            # Drought index guidelines
│   └── rag/                # RAG scripts & indexing utilities
├── voice/                  # Speech & Telephony services
│   ├── stt/                # Speech-to-text engines
│   ├── tts/                # Text-to-speech engines
│   ├── ivr/                # Call center flows
│   └── recordings/         # Audio clips
├── sms/                    # SMS Notification services
│   ├── providers/          # Twilio or Plivo integrations
│   ├── templates/          # Outgoing message templates
│   └── logs/               # SMS dispatch logs
├── data/                   # Git-ignored local database storage
│   ├── farmers/            # Cache for profile data
│   ├── conversations/      # Local conversation history
│   ├── market_cache/       # Cache for crop prices
│   ├── weather_cache/      # Cache for forecasts
│   └── vector_db/          # Persistent Chroma DB storage
├── deployment/             # Deployment configurations
│   ├── docker/             # Dockerfiles (backend & frontend)
│   ├── render/             # Render configuration
│   ├── vercel/             # Vercel configuration
│   └── nginx/              # Reverse proxy rules
├── docs/                   # Architectural & guide documentation
└── scripts/                # Setup & administration scripts
```
