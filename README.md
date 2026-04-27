# 🏭 Nexus-Giga

## Enterprise Multi-Agent Supply Chain & Maintenance Orchestrator

Nexus-Giga is an autonomous, multi-agent ecosystem designed for industrial giga-factories. It bridges gap between unstructured technical knowledge (PDF manuals) and structured enterprise data(telemetry, SQL databases) to fully automate the equipment maintenance and procurement lifecycle.

### 📊 Project Status

- [✅] **Phase 1: The Secure Data Bridge** (Complete)
- [ ] **Phase 2: Enterprise Knowledge & Memory** (Up Next)
- [ ] **Phase 3: The Multi-Agent**
- [ ] **Phase 4: Streaming & UX**
- [ ] **Phase 5: Evaluation & Production**

## 🏗️ Architecture & Tech Stack (Phase 1)

Currently, this repository contains the foundational **Secure Data Bridge**:

- **Database:** SQLite (Read-Only Mode for LLM safety)

- **Data Protocol:** Model context Protocol (MCP) using the Python SDK

- **Purpose:** Securely exposes local SQL inventory and telemtry data (e.g., equipment status, stock levels) to cloud-based LLMs without granting direct database write access.  

How to Run Locally (Phase 1)

1. **Activate Virtrual Environment:**

```bash
source venv/bin/activate
```

2. **Initialize Mock Database:**

```bash
python init_db.py
```

3. **Test the MCP Server:**

```bash
npx @modelcontextprotocol/inspector python backend/mcp/mcp_server.py
```


