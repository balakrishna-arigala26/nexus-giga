import asyncio
import json
import httpx
from fastapi import FastAPI, Query, Request
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

async def a2a_stream_generator(query: str, request: Request):
    """Connects to the local A2A server and streams the diagnostic report."""
    try:
        # Revert to 127.0.0.1 since we are now sharing the host network
        client = await ClientFactory.connect("http://127.0.0.1:8000")
        client._transport.httpx_client.timeout = httpx.Timeout(120.0)        
        
        yield f"data: {json.dumps({'status': 'connected', 'message': 'Connected to A2A Orchestrator...'})}\n\n"
        
        msg = create_text_message_object(content=query)
        yield f"data: {json.dumps({'status': 'processing', 'message': 'Agent is diagnosing the issue...'})}\n\n"
        
        current_report_len = 0
        
        try:
            async for chunk in client.send_message(msg):
                # 🛡️ Check if the user closed the browser tab mid-stream
                if await request.is_disconnected():
                    return

                # KEEP-ALIVE PING
                yield ": ping\n\n"
                
                if chunk:
                    extracted = extract_deep_strings(chunk)
                    valid_reports = [s for s in extracted if "Diagnostic" in s or "Equipment Status" in s]
                    
                    if valid_reports:
                        latest_report = max(valid_reports, key=len)
                        
                        # Calculate the diff! If it grew, we have new tokens.
                        if len(latest_report) > current_report_len:
                            new_text = latest_report[current_report_len:]
                            current_report_len = len(latest_report)
                            
                            # Stream ONLY the new characters
                            yield f"data: {json.dumps({'status': 'chunk', 'text': new_text})}\n\n"
                            await asyncio.sleep(0.01) # Force network flush
        except Exception:
            pass 
        
        # Send the final completion message to the frontend
        yield f"data: {json.dumps({'status': 'complete', 'message': 'Done'})}\n\n"
        
        # 🚀 THE FIX: Do not hang up the socket! Wait for React's eventSource.close() to hang up first.
        while True:
            if await request.is_disconnected():
                break # React successfully hung up, we can exit gracefully
            await asyncio.sleep(0.5)
                
    except asyncio.CancelledError:
        # The connection was successfully and gracefully closed by the client
        pass
    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

# ✨ Notice we added 'request: Request' here to track the connection state
@app.get("/api/diagnose")
async def diagnose_endpoint(request: Request, query: str = Query(..., description="The user's diagnostic query")):
    """FastAPI endpoint that returns a Server-Sent Events (SSE) stream."""
    return StreamingResponse(
        a2a_stream_generator(query, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("🌐 Starting Nexus-Giga Phase 4 API on Port 5000...")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)