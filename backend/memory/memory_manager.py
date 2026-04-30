import os
from dotenv import load_dotenv
from mem0 import Memory

# 1. Load Environment Variables
load_dotenv()

def seed_historical_memory():
    print("Initializing Mem0 Enterprise Memory Layer...")
    
    # 2. Configure Mem0 explicitly to avoid the OpenAI parameter error
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini"
            }
        }
    }
    
    # Initialize Mem0 with our explicit configuration
    m = Memory.from_config(config_dict=config)

    print("Injecting historical maintenance tickets into long-term memory...\n")
    
    # 3. Mock historical tickets for the V-101 Vacuum Gripper
    tickets = [
        "Ticket #882: V-101 Vacuum Gripper experienced ERR-V101-01 on 2026-03-15. Resolved by replacing the worn polyurethane suction pad.",
        "Ticket #904: V-101 Vacuum Gripper reported low pressure on 2026-04-02. Diagnostics revealed a clogged intake filter. Cleansed with compressed air."
    ]

    # 4. Store the memories tied to a specific "user" or "system" ID
    for ticket in tickets:
        m.add(ticket, user_id="nexus_maintenance_system")
        print(f"Stored: {ticket}")

    print("\nExecuting a test search to verify memory retrieval...")
    
    # Using the 'filters' dictionary for the new Mem0 API syntax
    response = m.search(
        "What issues has the V-101 had recently?", 
        filters={"user_id": "nexus_maintenance_system"}
    )
    
    print("\n--- Memory Retrieval Results ---")
    
    # FIXED: Extracting the actual list from the new 'results' key
    memory_list = response.get("results", [])
    
    for res in memory_list:
        print(f"-> {res['memory']}")
        
    print("\n✅ Phase 2 Complete: Mem0 Long-Term Memory is online!")

if __name__ == "__main__":
    seed_historical_memory()