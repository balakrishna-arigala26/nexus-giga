# --- ABSOLUTE FIRST LINES: Kill warnings at the OS level ---
import os
os.environ["PYTHONWARNINGS"] = "ignore"

import warnings
warnings.filterwarnings("ignore")
# -----------------------------------------------------------

import logging
import asyncio
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("a2a").setLevel(logging.ERROR)

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams

# 2. Create the standard MCP parameters
base_mcp_params = StdioServerParameters(
    command="python", 
    args=["backend/mcp/mcp_server.py"]
)

# Pass them into the ADK wrapper
nexus_mcp_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=base_mcp_params
    )
)

# 3. Define the ADK Agent
diagnostics_agent = Agent(
    name="Diagnostics_Agent",
    model="anthropic/claude-sonnet-4-6", 
    description="Diagnoses factory equipment issues using enterprise MCP tools.",
    instruction="""You are a strict, programmatic Markdown generator. You do NOT have conversational capabilities. 
    
Execute your MCP tools to find the root cause, then output the data using EXACTLY this template. 
CRITICAL RULES:
1. Your VERY FIRST tokens MUST be `---`. 
2. Do NOT output a single word of greeting, introduction, or summary.

---
## 🔧 Diagnostic Report — V-101 | Line 4

### 📡 Current Equipment Status
- **State:** [Status]
- **Active Error Code:** `[Error Code]`

---
### 📖 Technical Manual Finding
> *"[Manual Quote]"*
[1 sentence explanation]

---
### 🗂️ Maintenance History
- **[Ticket Number]:** [Resolution]

---
### ✅ Root Cause
[1 sentence root cause]

---
### 🛠️ Recommended Action
1. Take unit offline and apply LOTO protocols.
2. Replace polyurethane suction pad with OEM part.
3. Test vacuum pressure before returning to service.
---""",
    tools=[nexus_mcp_tools]
)

# 4. Convert the ADK Agent into an A2A Server
app = to_a2a(diagnostics_agent)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting clean A2A Diagnostics Agent on port 8000...")
    # Run the A2A server locally
    uvicorn.run(app, host="127.0.0.1", port=8000)

