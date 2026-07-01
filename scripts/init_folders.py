import os

dirs = [
    "backend/app/api",
    "backend/app/config",
    "backend/app/core",
    "backend/app/database",
    "backend/app/dependencies",
    "backend/app/middleware",
    "backend/app/models",
    "backend/app/orchestrator",
    "backend/app/prompts",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/utils",
    "backend/agents/base",
    "backend/agents/planner",
    "backend/agents/market",
    "backend/agents/weather",
    "backend/agents/disease",
    "backend/agents/schemes",
    "backend/agents/finance",
    "backend/agents/irrigation",
    "backend/agents/soil",
    "backend/agents/translation",
    "backend/agents/memory",
    "backend/agents/verifier",
    "backend/tests",
    "frontend/app",
    "frontend/components",
    "frontend/hooks",
    "frontend/lib",
    "frontend/public",
    "frontend/services",
    "frontend/styles",
    "knowledge/crops",
    "knowledge/diseases",
    "knowledge/fertilizers",
    "knowledge/pesticides",
    "knowledge/government_schemes",
    "knowledge/market",
    "knowledge/weather",
    "knowledge/rag",
    "voice/stt",
    "voice/tts",
    "voice/ivr",
    "voice/recordings",
    "sms/providers",
    "sms/templates",
    "sms/logs",
    "data/farmers",
    "data/conversations",
    "data/market_cache",
    "data/weather_cache",
    "data/vector_db",
    "docs/architecture",
    "docs/api",
    "docs/diagrams",
    "docs/roadmap",
    "docs/competition",
    "deployment/docker",
    "deployment/render",
    "deployment/vercel",
    "deployment/nginx",
    "scripts"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    if d.startswith("backend"):
        if d != "backend/tests":
            # Python package
            with open(os.path.join(d, "__init__.py"), "w") as f:
                pass
        else:
            with open(os.path.join(d, ".gitkeep"), "w") as f:
                pass
    else:
        with open(os.path.join(d, ".gitkeep"), "w") as f:
            pass

print("Successfully initialized Kisan Mitra AI repository folders.")
