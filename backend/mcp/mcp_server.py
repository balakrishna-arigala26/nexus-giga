import sqlite3
import json
import logging
from pathlib import Path
from  mcp.server.fastmcp import FastMCP

# ----------------------------------------------------------------------------
# Architecture Configuration
# ----------------------------------------------------------------------------
# Resolve the path to the data directory dynamically based on the Master Plan
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "factory_inventory.db"

# Configure logging for observability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Nexus-Giga-MCP")

# Initialize the MCP Server
# This is the bridge that the Diagnostics and Procurement agents will talk to.
mcp = FastMCP("Nexus-Giga-Facility-Data")

# -----------------------------------------------------------------------------
# Database Helper
# -----------------------------------------------------------------------------
def execute_query(query: str, params: tuple = ()) -> list[dict]:
    """Helper function to execute read-only queries against the SQLite DB."""
    try:
        # uri=True and mode=ro ensures the LLM cannot accidentally execute destructive operations
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Database query failed: {str(e)}")
        return [{"error": f"Database error: {str(e)}"}]
    
# ----------------------------------------------------------------------------
# MCP Tool Definitions (Exposed to the Multi-Agent Brain)
# ----------------------------------------------------------------------------
@mcp.tool()
def get_equipment_status(equipment_id: str) -> str:
    """
    Check the real-time operational status and maintenance history of a specific factory machine or part.

    Args:
        equipment_id: The unique ID of the equipment (e.g., 'V-101', 'M-204').
    """
    # SANITIZATION: remove accidental  newlines or sapces
    clean_id = equipment_id.strip()
    logger.info(f"Agent requested status for equipment: {clean_id}")

    query = "SELECT id, name, status, last_maintenance FROM equipment WHERE id = ?"
    results = execute_query(query, (clean_id,))

    if not results:
        return json.dumps({"error": f"Equipment ID '{clean_id}' not found in telemetry logs."})
    return json.dumps(results[0], indent=2)

@mcp.tool()
def check_inventory_level(part_name: str) -> str:
    """
    Check the local SQL inventory for the stock levels of a specific part before drafting a Purchase Order.
    
    Args:
        part_name: The name or partial name of the part (e.g., 'Vacuum Gripper').
    """
    # SANITIZATION: Remove accidental newlines or spaces
    clean_name = part_name.strip()
    logger.info(f"Agent requested inventory check for: {clean_name}")

    # Use LIKE for flexible matching since the agent might not know the exact string
    query = "SELECT id, name, stock_level FROM equipment WHERE name LIKE ?"
    results = execute_query(query, (f"%{clean_name}%",))

    if not results:
        return json.dumps({"error": f"No inventory found matching '{clean_name}'."})
    
    return json.dumps(results, indent=2)

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Initializing Nexus-Giga MCP Server via Standard Input/Output....")
    # Run the server using standard I/O (the default transport protocol for local MCP processes)
    mcp.run()