import asyncio
import json
import httpx
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from a2a.client import ClientFactory
from a2a.client.helpers import create_text_message_object

# Initialize FastAPI
app = FastAPI(title="Nexus-Giga Streaming API")

# Add CORS Middleware so Next.js on port 3000 can talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
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
    
    if isinstance(obj, str):
        found_strings.append(obj)
        return found_strings
        
    if isinstance(obj, dict):
        for v in obj.values():
            found_strings.extend(extract_deep_strings(v, visited))
        return found_strings
        
    if isinstance(obj, (list, tuple)):
        for item in obj:
            found_strings.extend(extract_deep_strings(item, visited))
        return found_strings

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
        # Revert to 127.0.0.1 since we are now sharing the host network
        client = await ClientFactory.connect("http://127.0.0.1:8000")
        client._transport.httpx_client.timeout = httpx.Timeout(120.0)        
        
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Connected to A2A Orchestrator...'})}\n\n"
        
        msg = create_text_message_object(content=query)
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Agent is diagnosing the issue...'})}\n\n"
        
        all_extracted_strings = set()
        
        try:
            async for chunk in client.send_message(msg):
                # KEEP-ALIVE PING: Sends an invisible SSE comment to stop browser timeouts
                yield ": ping\n\n"
                
                if chunk:
                    extracted = extract_deep_strings(chunk)
                    all_extracted_strings.update(extracted)
        except Exception:
            pass 
        
        valid_reports = [s for s in all_extracted_strings if "Diagnostic" in s and "Equipment Status" in s]
        
        if valid_reports:
            full_report = max(valid_reports, key=len)
            clean_text = full_report.replace("---", "").strip()
            yield f"data: {json.dumps({'status': 'complete', 'result': clean_text})}\n\n"
        else:
            yield f"data: {json.dumps({'status': 'error', 'message': 'Report generated but could not be cleanly extracted.'})}\n\n"
            
        # GRACEFUL CLOSE: Give the browser 2 seconds to parse the final JSON before shutting the socket down
        await asyncio.sleep(2)
                
    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

@app.get("/api/diagnose")
async def diagnose_endpoint(query: str = Query(..., description="The user's diagnostic query")):
    """FastAPI endpoint that returns a Server-Sent Events (SSE) stream."""
    return StreamingResponse(
        a2a_stream_generator(query),
        media_type="text/event-stream",
        headers={
            # STRICT HEADERS: Force the browser to process the stream immediately
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting Nexus-Giga Phase 4 API on Port 5000...")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)