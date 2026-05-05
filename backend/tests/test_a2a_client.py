import asyncio
import httpx
from a2a.client import ClientFactory
from a2a.client.helpers import create_text_message_object

async def test_agent():
    print("🔗 Connecting to local A2A server...")
    # 1. Connect using the official ClientFactory
    client = await ClientFactory.connect("http://127.0.0.1:8000")
    
    # Increase the network timeout to 120 seconds
    client._transport.httpx_client.timeout = httpx.Timeout(120.0)
    
    # Verify connection by fetching the generated Agent Card
    card = await client.get_card()
    print(f"✅ Connected to: {card.name}\n")
    
    print("📡 Transmitting issue to Diagnostics Agent... (Waiting for AI to think...)")
    
    # 2. Format the message securely 
    msg = create_text_message_object(
        content="The V-101 Vacuum Gripper on Line 4 stopped working and is flashing ERR-V101-01. Can you diagnose this?"
    )
    
    # 3. Stream the A2A response cleanly
    print("\n🏁 FINAL DIAGNOSTIC REPORT:\n")
    print("-" * 50)
    
    async for response in client.send_message(msg):
        # The A2A protocol returns a tuple: (Task_Object, None)
        task = response[0] 
        
        # Check if the task contains any final artifacts
        if hasattr(task, 'artifacts') and task.artifacts:
            for artifact in task.artifacts:
                if hasattr(artifact, 'parts') and artifact.parts:
                    for part in artifact.parts:
                        # Print only the clean, final text response
                        if hasattr(part.root, 'text'):
                            raw_text = part.root.text
                            # STRICT PARSER: Slice off any conversational garbage before the first '---'
                            clean_text = raw_text[raw_text.find("---"):] if "---" in raw_text else raw_text
                            
                            print(clean_text)
    
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_agent())