import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Load API Keys
load_dotenv()

class EnterpriseDiagnosticsAgent:
    def __init__(self):
        print("Initializing Enterprise Diagnostics Agent (Claude Sonnet 4.6)...")
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-6"
        
        self.tools = [
            {
                "name": "get_equipment_status",
                "description": "Check the real-time operational status of a factory machine.",
                "input_schema": {
                    "type": "object",
                    "properties": {"equipment_id": {"type": "string"}}
                }
            },
            {
                "name": "search_technical_manual",
                "description": "Search the Pinecone vector database for official equipment manuals.",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}}
                }
            },
            {
                "name": "check_memory_history",
                "description": "Query Mem0 for historical maintenance tickets.",
                "input_schema": {
                    "type": "object",
                    "properties": {"machine_id": {"type": "string"}}
                }
            }
        ]

    def execute_tool(self, tool_name, tool_input):
        """Simulating the data return from our Phase 1 & 2 databases"""
        print(f"⚙️  Executing Database Query: {tool_name} with {tool_input}")
        
        if tool_name == "get_equipment_status":
            return json.dumps({"status": "Offline - Error Code Active", "uptime": "99.2%"})
        elif tool_name == "search_technical_manual":
            return json.dumps({"resolution": "ERR-V101-01 indicates a worn polyurethane suction pad. Resolution: Replace the pad."})
        elif tool_name == "check_memory_history":
            return json.dumps({"history": "Ticket #882: V-101 replaced worn suction pad on 2026-03-15."})
        
        return "No data found."

    def analyze_issue(self, issue_description: str):
        print(f"\n[Diagnostics Agent] Received Issue: {issue_description}")
        print("[Diagnostics Agent] Thinking and selecting tools...\n")
        
        messages = [{"role": "user", "content": issue_description}]
        
        # Step 1: Claude decides which tools to use
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system="You are an expert Industrial Diagnostics Agent. You MUST use your provided tools to look up machine status, manual documentation, and historical memory before providing a resolution.",
            tools=self.tools,
            messages=messages
        )
        
        # Step 2: Execute the tools and return the data to Claude
        if response.stop_reason == "tool_use":
            # Append Claude's tool request to the conversation history
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for content in response.content:
                if content.type == "tool_use":
                    # Run our Python function
                    result_data = self.execute_tool(content.name, content.input)
                    
                    # Package the result for Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result_data
                    })
            
            # Send the database results back to Claude
            messages.append({"role": "user", "content": tool_results})
            
            print("\n[Diagnostics Agent] Synthesizing final resolution based on tool data...\n")
            
            # Step 3: Claude generates the final answer
            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system="You are an expert Industrial Diagnostics Agent. Give a clear, concise resolution based ONLY on the data provided by the tools.",
                tools=self.tools,
                messages=messages
            )
            
            print("--- FINAL AGENT RESOLUTION ---")
            print(final_response.content[0].text)

if __name__ == "__main__":
    agent = EnterpriseDiagnosticsAgent()
    agent.analyze_issue("The V-101 Vacuum Gripper just threw an ERR-V101-01 code. What does this mean and how did we fix it last time?")