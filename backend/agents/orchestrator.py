import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from anthropic import Anthropic
from google import genai

# Load API Keys
load_dotenv()

# ==========================================
# 1. Define Strict Data Structures (Pydantic)
# ==========================================
class DiagnosticReport(BaseModel):
    machine_id: str = Field(description="The ID of the machine.")
    error_code: str = Field(description="The exact error code.")
    root_cause: str = Field(description="The underlying cause of the failure.")
    required_part: str = Field(description="The specific part needed to fix the machine.")
    priority: str = Field(description="Priority level: HIGH, MEDIUM, or LOW.")

class PurchaseOrder(BaseModel):
    po_number: str = Field(description="A generated purchase order number (e.g., PO-2026-XXXX).")
    machine_id: str = Field(description="The machine this part is for.")
    part_name: str = Field(description="The exact name of the part to order.")
    quantity: int = Field(description="The number of parts to order (default to 2 for critical spares).")
    justification: str = Field(description="Brief reason for the order based on diagnostics.")

# ==========================================
# 2. Define the Multi-Agent Orchestrator
# ==========================================
class NexusOrchestrator:
    def __init__(self):
        print("Initializing Nexus-Giga Central Orchestrator...")
        # Initialize Anthropic (Claude) for heavy reasoning
        self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.claude_model = "claude-sonnet-4-6"
        
        # Initialize Google (Gemini) for high-speed triage
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def run_triage_agent(self, issue: str) -> str:
        print("\n[Orchestrator] 🚦 Routing issue to Gemini Triage Agent...")
        
        system_instruction = (
            "You are the Triage Agent for an industrial factory. Classify the following issue "
            "into exactly one of these two categories:\n"
            "1. 'MAINTENANCE' (if it involves broken machines, error codes, or factory equipment)\n"
            "2. 'GENERAL' (if it is about HR, cafeteria, scheduling, or non-equipment topics)\n"
            "Output ONLY the category name (MAINTENANCE or GENERAL)."
        )
        
        response = self.gemini_client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=f"{system_instruction}\n\nIssue: {issue}"
        )
        
        classification = response.text.strip().upper()
        
        # Safeguard to ensure clean routing
        if "MAINTENANCE" in classification:
            classification = "MAINTENANCE"
        elif "GENERAL" in classification:
            classification = "GENERAL"
        else:
            classification = "MAINTENANCE" # Default to maintenance if the model is unsure
            
        print(f"✅ [Triage Agent] Issue classified as: {classification}")
        return classification

    def run_diagnostics_agent(self, issue: str) -> str:
        print("\n[Orchestrator] 🚀 Routing issue to Diagnostics Agent (Claude)...")
        
        simulated_context = """
        Database Status: Offline (ERR-V101-01)
        Manual Context: ERR-V101-01 means worn polyurethane suction pad.
        Memory History: Ticket #882 fixed this by replacing the suction pad.
        """
        
        prompt = f"Analyze this issue: '{issue}'. Here is the system context: {simulated_context}. Return a structured diagnostic report."
        
        response = self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=1024,
            system="You are the Diagnostics Agent. Extract the machine ID, error code, root cause, required part, and priority based strictly on the provided context.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        report = response.content[0].text
        print(f"✅ [Diagnostics Agent] Report Generated:\n{report}\n")
        return report

    def run_procurement_agent(self, diagnostic_report: str) -> str:
        print("[Orchestrator] 🤝 Handing off context to Procurement Agent (Claude)...")
        
        schema_instructions = json.dumps(PurchaseOrder.model_json_schema(), indent=2)
        prompt = f"Based on this diagnostic report, draft a Purchase Order: \n{diagnostic_report}"
        
        system_instruction = (
            "You are the Procurement Agent. You strictly output ONLY raw, valid JSON. "
            "Do not use any markdown formatting or code blocks. "
            f"Your output MUST match this exact schema:\n{schema_instructions}"
        )
        
        response = self.claude_client.messages.create(
            model=self.claude_model,
            max_tokens=1024,
            system=system_instruction,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text

    def process_factory_issue(self, issue: str):
        print("\n==================================================")
        print(f"🚨 NEW FACTORY ISSUE DETECTED: {issue}")
        print("==================================================")
        
        # Step 0: Front Door Triage (Gemini)
        triage_category = self.run_triage_agent(issue)
        
        if triage_category == "GENERAL":
            print("\nℹ️  [System] This is a general inquiry. Routing to standard HR/Support DB...")
            print("🏁 ORCHESTRATION WORKFLOW COMPLETE (No maintenance required)")
            print("==================================================\n")
            return
            
        # Step 1: Agent 1 (Diagnostics)
        diagnostics_output = self.run_diagnostics_agent(issue)
        
        # Step 2: Agent-to-Agent Handoff -> Agent 2 (Procurement)
        po_output_json = self.run_procurement_agent(diagnostics_output)
        
        print("✅ [Procurement Agent] Purchase Order Drafted:")
        
        clean_json = po_output_json.replace("```json", "").replace("```", "").strip()
        
        try:
            po_dict = json.loads(clean_json)
            validated_po = PurchaseOrder(**po_dict)
            print(validated_po.model_dump_json(indent=4))
        except Exception as e:
            print(f"Failed to parse or validate JSON. Error: {e}")
            print("Raw output:")
            print(po_output_json)
            
        print("==================================================")
        print("🏁 ORCHESTRATION WORKFLOW COMPLETE")
        print("==================================================")

if __name__ == "__main__":
    orchestrator = NexusOrchestrator()
    
    # Test 1: A general question that should NOT trigger Claude
    orchestrator.process_factory_issue("When does the cafeteria serve lunch today?")
    
    # Test 2: A legitimate machine failure that should trigger the full A2A pipeline
    orchestrator.process_factory_issue("The V-101 Vacuum Gripper on Line 4 stopped working and is flashing ERR-V101-01.")