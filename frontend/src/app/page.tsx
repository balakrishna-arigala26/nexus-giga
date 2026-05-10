"use client";

import { useState, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [query, setQuery] = useState("The V-101 Vacuum Gripper on Line 4 stopped working.");
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [markdownOutput, setMarkdownOutput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  
  // We use a ref to hold the connection so we can safely close it if needed
  const eventSourceRef = useRef<EventSource | null>(null);

  const runDiagnostics = () => {
    if (!query) return;

    // 1. Reset the UI State
    setMarkdownOutput("");
    setStatusMessages(["Connecting to A2A Orchestrator..."]);
    setIsRunning(true);

    // 2. Safely close any hanging connections
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // 3. Initialize the Server-Sent Events (SSE) Stream
    const encodedQuery = encodeURIComponent(query);
    const eventSource = new EventSource(`http://127.0.0.1:5000/api/diagnose?query=${encodedQuery}`);
    eventSourceRef.current = eventSource;

    // 4. Listen to the stream in real-time
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.status === "connected") {
        setStatusMessages((prev) => [...prev, `[✓] ${data.message}`, "Routing to Diagnostics Agent..."]);
      } 
      else if (data.status === "processing") {
        setStatusMessages((prev) => [...prev, `[✓] System RAG initialized.`, `> ${data.message}`]);
      } 
      else if (data.status === "complete") {
        setStatusMessages((prev) => [...prev, "[✓] Diagnostics complete. Terminating connection."]);
        
        // Strip our deterministic Markdown delimiter and set the final output
        const cleanMarkdown = data.result.replace(/^---\s*\n*/, "");
        setMarkdownOutput(cleanMarkdown);
        
        eventSource.close();
        setIsRunning(false);
      } 
      else if (data.status === "error") {
        setStatusMessages((prev) => [...prev, `[ERROR] ${data.message}`]);
        eventSource.close();
        setIsRunning(false);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setStatusMessages((prev) => [...prev, "[ERROR] Connection to API lost."]);
      eventSource.close();
      setIsRunning(false);
    };
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-300 p-8 font-sans">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <header className="mb-8 border-b border-slate-700 pb-4">
          <h1 className="text-3xl font-bold text-blue-400">
            Nexus-Giga <span className="text-slate-500 font-light">| A2A Diagnostic Console</span>
          </h1>
          <p className="text-slate-400 mt-2">Enterprise Multi-Agent Orchestrator</p>
        </header>

        {/* Input Section */}
        <div className="bg-slate-800 rounded-lg p-6 shadow-xl border border-slate-700 mb-6">
          <label htmlFor="query" className="block text-sm font-medium text-slate-400 mb-2">
            Issue Description / Telemetry Data
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-600 rounded-md px-4 py-2 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              disabled={isRunning}
            />
            <button
              onClick={runDiagnostics}
              disabled={isRunning}
              className={`px-6 py-2 rounded-md font-medium transition-colors flex items-center gap-2 ${
                isRunning 
                  ? "bg-blue-800 text-slate-400 cursor-not-allowed" 
                  : "bg-blue-600 hover:bg-blue-700 text-white"
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
              {isRunning ? "Diagnosing..." : "Run Diagnostics"}
            </button>
          </div>
        </div>

        {/* Terminal / Output Section */}
        <div className="bg-black rounded-lg shadow-2xl border border-slate-700 overflow-hidden min-h-[400px] flex flex-col">
          
          {/* Terminal Header */}
          <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>

          {/* Terminal Body */}
          <div className="p-6 flex-1 overflow-y-auto">
            {/* Real-time Status Stream */}
            <div className="text-sm font-mono text-emerald-400 mb-4">
              {statusMessages.length === 0 ? "Ready for input..." : statusMessages.map((msg, idx) => (
                <div key={idx}>{msg}</div>
              ))}
              {isRunning && <span className="animate-pulse">_</span>}
            </div>

            {/* Rendered Markdown Output */}
            {markdownOutput && (
              <div className="markdown-body text-slate-300 font-sans mt-6 pt-6 border-t border-slate-800">
                <ReactMarkdown>{markdownOutput}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}