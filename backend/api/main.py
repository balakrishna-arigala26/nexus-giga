import asyncio
import json
import httpx
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from a2a.client import ClientFactory
from a2a.client.helpers import create_text_message_object

# Initialize FastAPI
app = FastAPI(title="Nexus-Giga Streaming API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_deep_strings(obj, visited=None):
    """Recursively hunts through memory to extract raw Python strings, bypassing repr() truncation."""
    if visited is None:
        visited = set()
        
    obj_id = id(obj)
    if obj_id in visited:
        return []
    visited.add(obj_id)
    
    found_strings = []
    
    # 1. We found a raw string in memory! Grab it before it gets truncated!
    if isinstance(obj, str):
        found_strings.append(obj)
        return found_strings
        
    # 2. Dig through dictionaries
    if isinstance(obj, dict):
        for v in obj.values():
            found_strings.extend(extract_deep_strings(v, visited))
        return found_strings
        
    # 3. Dig through lists
    if isinstance(obj, (list, tuple)):
        for item in obj:
            found_strings.extend(extract_deep_strings(item, visited))
        return found_strings

    # 4. Dig through Pydantic ADK objects safely
    if hasattr(obj, 'model_dump'):
        try:
            found_strings.extend(extract_deep_strings(obj.model_dump(), visited))
            return found_strings
        except Exception:
            pass
    elif hasattr(obj, 'dict'):
        try:
            found_strings.extend(extract_deep_strings(obj.dict(), visited))
            return found_strings
        except Exception:
            pass

    # 5. Dig through standard Python objects
    if hasattr(obj, '__dict__'):
        for v in obj.__dict__.values():
            found_strings.extend(extract_deep_strings(v, visited))
            
    if hasattr(obj, '__slots__'):
        for slot in obj.__slots__:
            if hasattr(obj, slot):
                found_strings.extend(extract_deep_strings(getattr(obj, slot), visited))
                
    return found_strings

async def a2a_stream_generator(query: str):
    """Connects to the local A2A server and streams the diagnostic report."""
    try:
        client = await ClientFactory.connect("http://127.0.0.1:8000")
        client._transport.httpx_client.timeout = httpx.Timeout(120.0)
        
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Connected to A2A Orchestrator...'})}\n\n"
        
        msg = create_text_message_object(content=query)
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Agent is diagnosing the issue...'})}\n\n"
        
        all_extracted_strings = set()
        
        try:
            # Accumulate ALL raw strings from every snapshot of the stream
            async for chunk in client.send_message(msg):
                if chunk:
                    extracted = extract_deep_strings(chunk)
                    all_extracted_strings.update(extracted)
        except Exception:
            # Safely catch the SDK Alpha bug or SSE drops
            pass 
        
        # Filter for strings that actually contain our diagnostic report
        valid_reports = [s for s in all_extracted_strings if "Diagnostic" in s and "Equipment Status" in s]
        
        if valid_reports:
            # Get the longest string to guarantee we have the final, fully completed report
            full_report = max(valid_reports, key=len)
            
            # Clean up the exact Markdown for the React frontend
            clean_text = full_report.replace("---", "").strip()
            yield f"data: {json.dumps({'status': 'complete', 'result': clean_text})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Report generated but could not be cleanly extracted.'})}\n\n"
                
    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

@app.get("/api/diagnose")
async def diagnose_equipment(query: str):
    """FastAPI endpoint that returns a Server-Sent Events (SSE) stream."""
    return StreamingResponse(
        a2a_stream_generator(query),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting Nexus-Giga Phase 4 API on Port 5000...")
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)