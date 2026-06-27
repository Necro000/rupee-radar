"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield, Sparkles, Check, Database, RefreshCw, AlertCircle } from "lucide-react";
import { api, HealthCheckResponse, SessionResponse } from "../lib/api";
import DropZone from "../components/upload/DropZone";

export default function Home() {
  const router = useRouter();

  // Connection states
  const [healthStatus, setHealthStatus] = useState<"unchecked" | "checking" | "online" | "offline">("unchecked");
  const [healthDetails, setHealthDetails] = useState<HealthCheckResponse | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  // File processing states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processingState, setProcessingState] = useState<
    "idle" | "creating_session" | "uploading" | "analyzing" | "completed" | "error"
  >("idle");
  const [stepProgress, setStepProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Column Mapping states
  const [showMappingModal, setShowMappingModal] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [statementHeaders, setStatementHeaders] = useState<string[]>([]);
  const [manualMapping, setManualMapping] = useState<Record<string, string>>({
    date: "",
    description: "",
    debit: "",
    credit: "",
    amount: "",
    balance: ""
  });

  useEffect(() => {
    checkApiHealth();
    checkSavedSession();
  }, []);

  const checkApiHealth = async () => {
    setHealthStatus("checking");
    const startTime = performance.now();
    try {
      const data = await api.checkHealth();
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      setHealthStatus("online");
      setHealthDetails(data);
    } catch (error) {
      setHealthStatus("offline");
      setLatency(null);
      setHealthDetails(null);
      console.error(error);
    }
  };

  const checkSavedSession = () => {
    const saved = localStorage.getItem("rupeeradar_session");
    if (saved) {
      try {
        const session: SessionResponse = JSON.parse(saved);
        // If a session exists, check health first. We can let the user resume their session
        // by pushing them to the dashboard.
        router.push(`/dashboard/${session.sessionId}`);
      } catch (e) {
        localStorage.removeItem("rupeeradar_session");
      }
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setErrorMessage(null);
    setProcessingState("idle");
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setProcessingState("idle");
    setErrorMessage(null);
  };

  const startAutomaticPipeline = async () => {
    if (!selectedFile) return;

    setErrorMessage(null);
    setStepProgress(5);
    
    let sessionId = "";
    
    try {
      // Step 1: Create session
      setProcessingState("creating_session");
      setStepProgress(15);
      const sessionData = await api.createSession();
      sessionId = sessionData.sessionId;
      localStorage.setItem("rupeeradar_session", JSON.stringify(sessionData));

      // Step 2: Upload File
      setProcessingState("uploading");
      setStepProgress(40);
      await api.uploadStatement(sessionId, selectedFile);

      // Step 3: Run Analysis
      setProcessingState("analyzing");
      setStepProgress(70);
      await api.analyzeSession(sessionId);

      // Step 4: Verification / Poll check
      setStepProgress(95);
      const statusData = await api.getSessionStatus(sessionId);
      
      if (statusData.status === "error") {
        throw new Error(statusData.errorMessage || "Pipeline analysis returned an error status.");
      }

      setProcessingState("completed");
      setStepProgress(100);

      // Redirect to the dashboard
      setTimeout(() => {
        router.push(`/dashboard/${sessionId}`);
      }, 500);

    } catch (error: any) {
      console.error(error);
      if (error.detail?.error_code === "MAPPING_REQUIRED") {
        setActiveSessionId(sessionId);
        setStatementHeaders(error.detail.headers || []);
        
        // Pre-fill mapping fields from backend suggested mapping
        const suggested = error.detail.suggested_mapping || {};
        setManualMapping({
          date: suggested.date || "",
          description: suggested.description || "",
          debit: suggested.debit || "",
          credit: suggested.credit || "",
          amount: suggested.amount || "",
          balance: suggested.balance || ""
        });
        
        setShowMappingModal(true);
        setProcessingState("idle");
        return;
      }

      setProcessingState("error");
      setErrorMessage(error.message || "An unexpected error occurred during processing.");
      
      // Clean up failed session storage
      localStorage.removeItem("rupeeradar_session");
    }
  };

  const submitManualMapping = async () => {
    // Basic validation: must have date and at least one amount field
    if (!manualMapping.date) {
      alert("Please map the 'Date' column.");
      return;
    }
    if (!manualMapping.amount && !manualMapping.debit && !manualMapping.credit) {
      alert("Please map either 'Unified Amount' or 'Debit' and 'Credit' columns.");
      return;
    }

    setShowMappingModal(false);
    setProcessingState("analyzing");
    setStepProgress(75);
    setErrorMessage(null);
    
    try {
      await api.analyzeSession(activeSessionId, manualMapping);

      setStepProgress(95);
      const statusData = await api.getSessionStatus(activeSessionId);
      
      if (statusData.status === "error") {
        throw new Error(statusData.errorMessage || "Pipeline analysis returned an error status.");
      }

      setProcessingState("completed");
      setStepProgress(100);

      // Redirect to the dashboard
      setTimeout(() => {
        router.push(`/dashboard/${activeSessionId}`);
      }, 500);

    } catch (error: any) {
      console.error(error);
      setProcessingState("error");
      setErrorMessage(error.message || "An unexpected error occurred during manual mapping processing.");
      localStorage.removeItem("rupeeradar_session");
    }
  };

  return (
    <div className="flex-1 bg-gradient-to-br from-zinc-950 via-zinc-900 to-emerald-950 text-zinc-100 font-sans min-h-screen py-10 px-4 sm:px-6 lg:px-8 flex flex-col justify-between">
      {/* Header */}
      <header className="max-w-7xl mx-auto w-full flex items-center justify-between border-b border-zinc-800/80 pb-6 mb-10">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 font-bold text-zinc-950 text-xl shadow-lg shadow-emerald-500/20">
            ₹
            <span className="absolute inline-flex h-full w-full rounded-xl bg-emerald-400 opacity-20 animate-ping"></span>
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
              RupeeRadar
            </h1>
            <p className="text-[10px] text-zinc-400 font-semibold uppercase tracking-wider">Statement Analytics</p>
          </div>
        </div>

        {/* Connection status */}
        <div className="flex items-center gap-2">
          {healthStatus === "online" && (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 ring-1 ring-inset ring-emerald-500/20">
              <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              API Online ({latency}ms)
            </span>
          )}
          {healthStatus === "offline" && (
            <span className="inline-flex items-center rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-400 ring-1 ring-inset ring-red-500/20 animate-pulse">
              API Offline
            </span>
          )}
          {healthStatus === "checking" && (
            <span className="inline-flex items-center rounded-full bg-yellow-500/10 px-2.5 py-0.5 text-xs font-semibold text-yellow-400 ring-1 ring-inset ring-yellow-500/20">
              Checking...
            </span>
          )}
          <button
            onClick={checkApiHealth}
            className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition"
            title="Refresh Connection"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Main Area */}
      <main className="max-w-4xl mx-auto w-full flex-1 flex flex-col items-center justify-center py-10">
        <div className="text-center max-w-2xl mb-10">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-zinc-100">
            Understand your <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">spending patterns</span> instantly
          </h2>
          <p className="text-sm text-zinc-400 mt-3 leading-relaxed">
            Upload your messy PDF/CSV bank statement. RupeeRadar cleans descriptions, categorizes transactions via rules + Groq AI, identifies subscriptions, and generates visual charts.
          </p>
        </div>

        {/* Upload Interface */}
        {processingState === "idle" ? (
          <div className="w-full flex flex-col items-center gap-6">
            <DropZone
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
              onClear={handleClearFile}
            />
            {selectedFile && (
              <button
                onClick={startAutomaticPipeline}
                disabled={healthStatus === "offline"}
                className={`w-full max-w-md py-3 font-extrabold rounded-xl shadow-md transition text-sm cursor-pointer ${
                  healthStatus === "offline"
                    ? "bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700"
                    : "bg-emerald-500 text-zinc-950 hover:bg-emerald-400 active:scale-[0.98]"
                }`}
              >
                Analyze Statement
              </button>
            )}
          </div>
        ) : (
          /* Processing Loader View */
          <div className="w-full max-w-xl bg-zinc-900/60 border border-zinc-800 rounded-2xl p-8 backdrop-blur-md text-center flex flex-col items-center gap-6">
            <div className="relative flex items-center justify-center">
              <div className="h-14 w-14 border-4 border-emerald-500/20 border-t-emerald-400 rounded-full animate-spin"></div>
              <Sparkles className="w-5 h-5 text-emerald-400 absolute animate-pulse" />
            </div>

            <div className="w-full">
              <div className="flex justify-between text-xs font-semibold text-zinc-400 mb-2 px-1">
                <span>
                  {processingState === "creating_session" && "Initializing short-lived workspace..."}
                  {processingState === "uploading" && "Uploading document structure..."}
                  {processingState === "analyzing" && "Classifying categories & tracking EMIs..."}
                  {processingState === "completed" && "Loading dashboard..."}
                  {processingState === "error" && "Pipeline error occurred"}
                </span>
                <span>{stepProgress}%</span>
              </div>
              <div className="w-full bg-zinc-850 rounded-full h-2 overflow-hidden border border-zinc-800/80">
                <div 
                  className={`h-full rounded-full transition-all duration-300 ${
                    processingState === "error" ? "bg-red-500" : "bg-emerald-400"
                  }`} 
                  style={{ width: `${stepProgress}%` }}
                ></div>
              </div>
            </div>

            {processingState === "error" && (
              <div className="w-full flex flex-col items-center gap-4">
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-3.5 flex items-start gap-2.5 text-xs text-left w-full">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="font-bold">Error Info:</span>
                    <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
                  </div>
                </div>
                <button
                  onClick={handleClearFile}
                  className="px-5 py-2 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs font-bold hover:bg-zinc-750 transition"
                >
                  Retry Upload
                </button>
              </div>
            )}
          </div>
        )}

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl mt-16 border-t border-zinc-800/80 pt-10">
          <div className="flex gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 h-9 w-9 flex items-center justify-center flex-shrink-0">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-zinc-200">100% Client-First Privacy</h4>
              <p className="text-xs text-zinc-450 leading-relaxed mt-1">
                Statements are parsed in short-lived memory sessions. All files and records are purged after 24h or instantly upon manual deletion.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 h-9 w-9 flex items-center justify-center flex-shrink-0">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-zinc-200">Structured Extractor</h4>
              <p className="text-xs text-zinc-450 leading-relaxed mt-1">
                Correctly matches mixed dates, parses debit/credit columns, and strips UPI ID handles or merchant code strings automatically.
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 h-9 w-9 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-zinc-200">Rule-AI Categorizer</h4>
              <p className="text-xs text-zinc-450 leading-relaxed mt-1">
                Combines high-speed rules for standard bills with an LLM categorization fallback for messy unknown descriptions.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full text-center border-t border-zinc-800/80 pt-6 mt-10 text-[10px] text-zinc-500">
        RupeeRadar assistant client sandbox. No long-term storage is allocated for statement uploads.
      </footer>

      {showMappingModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-md p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-zinc-150">Manual Column Mapping</h3>
                <p className="text-[10px] text-zinc-400 font-medium">Heuristics failed to auto-detect columns. Please match them manually.</p>
              </div>
            </div>

            <div className="space-y-4 my-6">
              {/* Date Field (Required) */}
              <div>
                <label className="block text-xs font-bold text-zinc-350 mb-1">
                  Transaction Date <span className="text-emerald-400">*</span>
                </label>
                <select
                  value={manualMapping.date}
                  onChange={(e) => setManualMapping(prev => ({ ...prev, date: e.target.value }))}
                  className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                >
                  <option value="">-- Select Date Column --</option>
                  {statementHeaders.map((header) => (
                    <option key={header} value={header}>{header}</option>
                  ))}
                </select>
              </div>

              {/* Description Field */}
              <div>
                <label className="block text-xs font-bold text-zinc-350 mb-1">
                  Description / Narration Column
                </label>
                <select
                  value={manualMapping.description}
                  onChange={(e) => setManualMapping(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                >
                  <option value="">-- Select Description Column --</option>
                  {statementHeaders.map((header) => (
                    <option key={header} value={header}>{header}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Debit Column */}
                <div>
                  <label className="block text-xs font-bold text-zinc-350 mb-1">
                    Debit / Withdrawal Column
                  </label>
                  <select
                    value={manualMapping.debit}
                    onChange={(e) => setManualMapping(prev => ({ ...prev, debit: e.target.value }))}
                    className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                  >
                    <option value="">-- None --</option>
                    {statementHeaders.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>

                {/* Credit Column */}
                <div>
                  <label className="block text-xs font-bold text-zinc-350 mb-1">
                    Credit / Deposit Column
                  </label>
                  <select
                    value={manualMapping.credit}
                    onChange={(e) => setManualMapping(prev => ({ ...prev, credit: e.target.value }))}
                    className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                  >
                    <option value="">-- None --</option>
                    {statementHeaders.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Single Amount Column */}
                <div>
                  <label className="block text-xs font-bold text-zinc-350 mb-1">
                    Unified Amount Column
                  </label>
                  <select
                    value={manualMapping.amount}
                    onChange={(e) => setManualMapping(prev => ({ ...prev, amount: e.target.value }))}
                    className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                  >
                    <option value="">-- None --</option>
                    {statementHeaders.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>

                {/* Balance Column */}
                <div>
                  <label className="block text-xs font-bold text-zinc-350 mb-1">
                    Running Balance Column
                  </label>
                  <select
                    value={manualMapping.balance}
                    onChange={(e) => setManualMapping(prev => ({ ...prev, balance: e.target.value }))}
                    className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                  >
                    <option value="">-- None --</option>
                    {statementHeaders.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-[10px] text-zinc-500 italic mt-2">
                * Note: Either "Unified Amount Column" OR both "Debit" and "Credit" columns must be mapped.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 mt-6 border-t border-zinc-800 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowMappingModal(false);
                  handleClearFile();
                }}
                className="px-4 py-2 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-350 hover:text-zinc-200 text-xs font-bold transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitManualMapping}
                className="px-5 py-2 rounded-xl bg-emerald-500 text-zinc-950 hover:bg-emerald-400 text-xs font-bold transition active:scale-95 cursor-pointer"
              >
                Run Analysis
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
