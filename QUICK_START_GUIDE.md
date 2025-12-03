# ⚡ Quick Start Guide

## 5-Minute Setup

### Step 1: Install (30 seconds)
```bash
pip install -r requirements_langgraph.txt
```

### Step 2: Environment (10 seconds)
```bash
export OPENAI_API_KEY="your-key"
```

### Step 3: Test (30 seconds)
```bash
python test_complete_system.py
```

### Step 4: Start API (10 seconds)
```bash
uvicorn src.api.routes:app --reload --port 8000
```

### Step 5: Use API (10 seconds)
```bash
curl http://localhost:8000/health
```

**Done! Your system is running!** 🚀

---

## Add Your First Agent (3 lines)
```python
from src.registry.agent_registry import register_agent

@register_agent(agent_id="my_agent", name="My Agent")
def my_agent(state):
    return {"result": "success"}
```

**That's it!** Your agent is now:
- Registered in the system
- Discoverable via API
- Ready to use in workflows

---

## Common Tasks

### List All Agents
```bash
curl http://localhost:8000/agents
```

### Compare Countries
```bash
curl -X POST "http://localhost:8000/api/v1/compare-countries?countries=USA&countries=DEU"
```

### Check Health
```bash
curl http://localhost:8000/health
```

### View API Docs
```
http://localhost:8000/docs
```

---

## Troubleshooting

### API won't start?
```bash
# Check port
lsof -i :8000

# Use different port
uvicorn src.api.routes:app --port 8001
```

### Tests failing?
```bash
# Clear cache
rm -rf **/__pycache__

# Run specific test
python test_registry.py
```

### Import errors?
```bash
# Check Python path
echo $PYTHONPATH

# Run from project root
cd roi_langgraph
python test_complete_system.py
```

---

**Need help? Check README_LANGGRAPH_SYSTEM.md**
