import os
import warnings

# ==========================================
# 🛑 SILENCE ALL THIRD-PARTY WARNINGS FIRST
# ==========================================
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)
warnings.filterwarnings("ignore")
# ==========================================

import asyncio
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.run_config import RunConfig

# Legacy imports to bypass Ragas Issue #2624
from ragas.metrics import Faithfulness, AnswerRelevancy 

# EXPLICIT INJECTION: Import modern Langchain models
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

# ==========================================
# 🏭 NEXUS-GIGA: 20-QUESTION STRESS TEST
# ==========================================
test_data = [
    {
        "question": "What is the active error code for the V-101 Vacuum Gripper on Line 4?",
        "ground_truth": "The active error code is ERR-V101-01.",
        "simulated_answer": "The V-101 Vacuum Gripper currently has an Active Error Code of ERR-V101-01.",
        "simulated_context": "V-101 Vacuum Gripper is located on Line 4. Current State: Offline. Active Error Code: ERR-V101-01."
    },
    {
        "question": "What line is the V-101 Vacuum Gripper located on?",
        "ground_truth": "It is located on Line 4.",
        "simulated_answer": "The V-101 Vacuum Gripper is stationed on Line 4.",
        "simulated_context": "Equipment Registry: V-101 Vacuum Gripper. Location assignment: Production Line 4."
    },
    {
        "question": "What is the current operational state of the V-101 Vacuum Gripper?",
        "ground_truth": "The operational state is Offline.",
        "simulated_answer": "Based on the telemetry data, the V-101 is currently Offline.",
        "simulated_context": "Telemetry check for V-101: Status is Offline. Last active: 45 minutes ago."
    },
    {
        "question": "Who is the manufacturer of the V-101 Vacuum Gripper?",
        "ground_truth": "The manufacturer is RoboTech Industries.",
        "simulated_answer": "The V-101 Vacuum Gripper is manufactured by RoboTech Industries.",
        "simulated_context": "V-101 Vacuum Gripper Manual. Manufacturer: RoboTech Industries. Model Year: 2024."
    },
    {
        "question": "What is the normal operating pressure for the V-101?",
        "ground_truth": "The normal operating pressure is 80 PSI.",
        "simulated_answer": "The V-101 operates normally at a pressure of 80 PSI.",
        "simulated_context": "Pneumatic specifications for V-101: Normal operating pressure is 80 PSI. Max safe pressure is 100 PSI."
    },
    {
        "question": "What is the part number for a replacement suction cup?",
        "ground_truth": "The replacement part number is SC-4055.",
        "simulated_answer": "If you need a replacement suction cup for the V-101, the part number is SC-4055.",
        "simulated_context": "Maintenance Parts List (V-101): Suction Cup Replacement Part # SC-4055."
    },
    {
        "question": "Are there any SC-4055 suction cups currently in inventory?",
        "ground_truth": "Yes, there are 12 units in inventory.",
        "simulated_answer": "Yes, I checked the inventory database. There are currently 12 SC-4055 units available.",
        "simulated_context": "Inventory Database Query: Part SC-4055. Stock level: 12 units. Location: Bin B-4."
    },
    {
        "question": "What is the maximum payload capacity of the V-101?",
        "ground_truth": "The maximum payload capacity is 15 kilograms.",
        "simulated_answer": "The V-101 Vacuum Gripper can safely lift a maximum payload of 15 kilograms.",
        "simulated_context": "V-101 Specifications: Max Payload Capacity: 15 kg. Grip force: 300N."
    },
    {
        "question": "What safety protocol must be followed before servicing the V-101?",
        "ground_truth": "You must lock out the main pneumatic valve.",
        "simulated_answer": "Before servicing, you must follow the safety protocol and lock out the main pneumatic valve.",
        "simulated_context": "Safety Manual Sec 4.1: Prior to servicing the V-101, operators must lock out the main pneumatic valve to prevent accidental actuation."
    },
    {
        "question": "When was the last routine maintenance performed on the V-101?",
        "ground_truth": "The last maintenance was on October 12th.",
        "simulated_answer": "The maintenance logs indicate the last routine service was completed on October 12th.",
        "simulated_context": "Maintenance Log V-101: Last routine inspection and filter replacement occurred on October 12th."
    },
    {
        "question": "What type of filter does the V-101 pneumatic system use?",
        "ground_truth": "It uses a HEPA-99 inline filter.",
        "simulated_answer": "The pneumatic system for the V-101 requires a HEPA-99 inline filter.",
        "simulated_context": "V-101 Pneumatic Guide: To prevent dust ingress, the system relies on a HEPA-99 inline filter."
    },
    {
        "question": "Which multi-agent framework orchestrates the AI logic?",
        "ground_truth": "Google ADK is used for orchestration.",
        "simulated_answer": "The multi-agent orchestration for Nexus-Giga is handled by Google ADK.",
        "simulated_context": "Architecture docs: Nexus-Giga uses Google ADK for production-ready Agent-to-Agent (A2A) handoffs."
    },
    {
        "question": "What protocol is used to securely expose the local factory databases?",
        "ground_truth": "The Model Context Protocol (MCP) is used.",
        "simulated_answer": "We use the Model Context Protocol (MCP) to securely connect the LLMs to the local factory databases.",
        "simulated_context": "Security Docs: The Model Context Protocol (MCP) securely exposes local DBs without giving the LLM direct SQL access."
    },
    {
        "question": "Which vector database stores the unstructured equipment manuals?",
        "ground_truth": "Pinecone is used to store the manuals.",
        "simulated_answer": "Pinecone is utilized as the vector database for unstructured PDF manuals.",
        "simulated_context": "Knowledge Retrieval Setup: LlamaIndex pairs with Pinecone for Hybrid Search of heavy technical PDFs."
    },
    {
        "question": "Which agent handles the ordering of out-of-stock parts?",
        "ground_truth": "The Procurement Agent handles ordering.",
        "simulated_answer": "The Procurement Agent is responsible for placing orders for out-of-stock items.",
        "simulated_context": "Agent Routing: Diagnostics Agent diagnoses issues. Procurement Agent orders missing parts."
    },
    {
        "question": "What security layer prevents hallucinatory advice from the agents?",
        "ground_truth": "NeMo Guardrails prevents hallucinations.",
        "simulated_answer": "NeMo Guardrails is implemented as the security layer to block hallucinatory advice.",
        "simulated_context": "Security Layer: NeMo Guardrails prevents prompt injection and hallucinatory advice in high-stakes environments."
    },
    {
        "question": "What is the recommended troubleshooting for ERR-V101-01?",
        "ground_truth": "Inspect the suction cup for debris.",
        "simulated_answer": "To troubleshoot ERR-V101-01, you should inspect the suction cup for debris and check for air leaks.",
        "simulated_context": "Error Code ERR-V101-01 (Low Suction): Step 1: Inspect suction cup for debris. Step 2: Check pneumatic lines for leaks."
    },
    {
        "question": "What is the maximum operating temperature for the V-101?",
        "ground_truth": "The maximum temperature is 45 degrees Celsius.",
        "simulated_answer": "The equipment can operate safely up to 45 degrees Celsius.",
        "simulated_context": "Environmental Specs V-101: Operating temperature range: 5 to 45 degrees Celsius."
    },
    {
        "question": "What power supply voltage does the V-101 controller require?",
        "ground_truth": "It requires 24V DC.",
        "simulated_answer": "The main controller for the V-101 requires a 24V DC power supply.",
        "simulated_context": "Electrical Specs: The logic controller runs on a standard 24V DC power supply."
    },
    {
        "question": "What system provides long-term episodic memory for the AI?",
        "ground_truth": "Mem0 provides long-term memory.",
        "simulated_answer": "Mem0 is integrated to provide the AI with long-term episodic memory.",
        "simulated_context": "Agent Memory Architecture: Mem0 provides long-term memory to recall historical factory maintenance tickets."
    }
]

async def run_evaluation():
    print(f"🧪 Starting Automated Evaluation Pipeline with {len(test_data)} Scenarios...")
    
    # 1. INITIALIZE the modern models
    judge_llm = ChatOpenAI(model="gpt-4o-mini")
    judge_embeddings = OpenAIEmbeddings()
    
    # 2. Extract arrays from our structured dictionary
    questions = [item["question"] for item in test_data]
    ground_truths = [item["ground_truth"] for item in test_data]
    answers = [item["simulated_answer"] for item in test_data]
    contexts = [[item["simulated_context"]] for item in test_data] # Ragas expects contexts as a list of lists

    data = {
        "user_input": questions,           
        "response": answers,               
        "retrieved_contexts": contexts,    
        "reference": ground_truths         
    }
    dataset = Dataset.from_dict(data)

    print("\n⚖️ Evaluating responses against Faithfulness and Relevance metrics...")
    print("🧠 (Throttling API requests to prevent OpenAI timeouts...)")
    
    # NEW: Configure Ragas to slow down and retry on errors
    safe_config = RunConfig(
        timeout=120,       # Give OpenAI 2 full minutes to respond per query
        max_workers=2,     # Only process 2 prompts at a time (prevents rate limits)
        max_retries=5      # If OpenAI drops it, try again 5 times before failing
    )

    # 3. PASS the config into the evaluate function
    result = evaluate(
        dataset,
        metrics=[
            Faithfulness(llm=judge_llm),
            AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings),
        ],
        run_config=safe_config  # <--- Inject config here
    )

    print("\n📊 Final Batch Evaluation Results:")
    print(result)
    
if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set. Make sure it is in your .env file.")
        exit(1)
        
    asyncio.run(run_evaluation())