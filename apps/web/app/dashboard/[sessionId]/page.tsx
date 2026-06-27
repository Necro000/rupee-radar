"use client";

import React, { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { 
  LayoutDashboard, 
  PieChart, 
  ListFilter, 
  Repeat, 
  Sparkles, 
  Trash2, 
  ArrowLeft,
  RefreshCw,
  AlertCircle,
  FileText
} from "lucide-react";
import { api, SummaryResponse, Insight } from "../../../lib/api";
import SummaryCards from "../../../components/dashboard/SummaryCards";
import CategoryChart from "../../../components/dashboard/CategoryChart";
import TransactionTable from "../../../components/dashboard/TransactionTable";
import RecurringList from "../../../components/dashboard/RecurringList";
import InsightCards from "../../../components/dashboard/InsightCards";

type TabType = "overview" | "categories" | "transactions" | "recurring" | "insights";

export default function DashboardPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const router = useRouter();
  const { sessionId } = use(params);

  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Poll state to confirm session is still alive
  const [sessionCheck, setSessionCheck] = useState<string | null>(null);

  // Period / Date Range states
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState<string>("");
  const [customRange, setCustomRange] = useState({ from: "", to: "" });

  useEffect(() => {
    loadDashboardData();
  }, [sessionId, fromDate, toDate]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Verify session status first
      const statusRes = await api.getSessionStatus(sessionId);
      setSessionCheck(statusRes.status);
      
      if (statusRes.status === "error") {
        throw new Error(statusRes.errorMessage || "The backend statement processing failed.");
      }

      // 2. Fetch summary and insights in parallel
      const [summaryRes, insightsRes] = await Promise.all([
        api.getSummary(sessionId, fromDate || undefined, toDate || undefined),
        api.getInsights(sessionId)
      ]);

      setSummary(summaryRes);
      setInsights(insightsRes);
    } catch (e: any) {
      console.error(e);
      if (e.status === 404 || e.message?.includes("Session not found or expired")) {
        localStorage.removeItem("rupeeradar_session");
      }
      setError(e.message || "Failed to load dashboard statistics. The session may have expired.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  const handleMonthChange = (month: string) => {
    setSelectedMonth(month);
    setCustomRange({ from: "", to: "" });
    if (!month) {
      setFromDate("");
      setToDate("");
      return;
    }
    const parts = month.split("-");
    if (parts.length < 2) return;
    const year = parts[0];
    const monthStr = parts[1];
    const y = parseInt(year);
    const m = parseInt(monthStr);
    
    // First day of month: YYYY-MM-01
    const fromStr = `${year}-${monthStr}-01`;
    // Last day of month
    const lastDay = new Date(y, m, 0).getDate();
    const lastDayStr = lastDay < 10 ? `0${lastDay}` : `${lastDay}`;
    const toStr = `${year}-${monthStr}-${lastDayStr}`;
    
    setFromDate(fromStr);
    setToDate(toStr);
  };

  const handleCustomRangeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSelectedMonth("");
    setFromDate(customRange.from);
    setToDate(customRange.to);
  };

  const handleDeleteSession = async () => {
    if (!confirm("Are you sure you want to delete this session? This will permanently purge your database records and statement files.")) {
      return;
    }

    try {
      await api.deleteSession(sessionId);
      localStorage.removeItem("rupeeradar_session");
      router.push("/");
    } catch (e: any) {
      alert(`Failed to delete session: ${e.message || e}`);
    }
  };

  const handleExportPDF = () => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.open(`${API_BASE_URL}/api/v1/sessions/${sessionId}/report?format=pdf`, "_blank");
  };

  if (loading) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col items-center justify-center min-h-screen text-zinc-400">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 border-4 border-emerald-500/25 border-t-emerald-400 rounded-full animate-spin"></div>
          <span className="text-sm font-semibold tracking-wider uppercase text-zinc-500">Loading Dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-6 text-center shadow-lg">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-zinc-100">Session Error</h3>
          <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{error}</p>
          <button
            onClick={() => {
              localStorage.removeItem("rupeeradar_session");
              router.push("/");
            }}
            className="w-full mt-6 py-2.5 bg-zinc-800 hover:bg-zinc-750 text-zinc-200 border border-zinc-700 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Upload</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-gradient-to-br from-zinc-950 via-zinc-900 to-emerald-950 text-zinc-100 font-sans min-h-screen py-8 px-4 sm:px-6 lg:px-8 flex flex-col justify-between">
      {/* Header Area */}
      <div className="max-w-7xl mx-auto w-full flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-zinc-800/80 pb-6 mb-8 gap-4">
        {/* Logo and Session Badge */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 font-bold text-zinc-950 text-lg shadow-md shadow-emerald-500/10">
            ₹
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black tracking-tight text-zinc-150">RupeeRadar</h1>
              <span className="text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-450 truncate max-w-[150px]" title={sessionId}>
                Session: {sessionId.substring(0, 8)}...
              </span>
            </div>
            <p className="text-[10px] text-zinc-400 font-semibold uppercase tracking-wider mt-0.5">Live Dashboard</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportPDF}
            className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:border-emerald-500/40 hover:bg-emerald-500/15 transition flex items-center gap-1.5 text-xs font-semibold cursor-pointer animate-in fade-in"
            title="Export compiled PDF report"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Export PDF</span>
          </button>

          <button
            onClick={handleRefresh}
            className="p-2 rounded-xl border border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 transition flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
            title="Reload metrics data"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>

          <button
            onClick={handleDeleteSession}
            className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20 hover:border-red-500/40 hover:bg-red-500/15 transition flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
            title="Purge session data"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Delete Session</span>
          </button>
        </div>
      </div>

      {/* Period / Date Range Selector Bar */}
      <div className="max-w-7xl mx-auto w-full bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-4 mb-6 backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Statement Period:</span>
          {fromDate && toDate ? (
            <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
              {fromDate} to {toDate}
            </span>
          ) : (
            <span className="text-xs font-bold text-zinc-450 bg-zinc-950 border border-zinc-850 px-2.5 py-1 rounded-lg">
              All Time Data
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Calendar Month Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-500">Filter Month</label>
            <select
              value={selectedMonth}
              onChange={(e) => handleMonthChange(e.target.value)}
              className="px-3 py-1.5 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-300 focus:outline-none focus:border-emerald-500 cursor-pointer animate-in fade-in"
            >
              <option value="">All Months</option>
              {summary?.monthlyAggregation?.map((item) => {
                const parts = item.month.split("-");
                if (parts.length < 2) return null;
                const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, 2);
                const label = d.toLocaleString("default", { month: "long", year: "numeric" });
                return (
                  <option key={item.month} value={item.month}>
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="h-4 w-px bg-zinc-800 hidden md:block"></div>

          {/* Custom Date Inputs */}
          <form onSubmit={handleCustomRangeSubmit} className="flex items-center gap-2">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-500">Custom Range</span>
            <input
              type="date"
              value={customRange.from}
              onChange={(e) => setCustomRange(prev => ({ ...prev, from: e.target.value }))}
              className="px-2 py-1 text-xs bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-emerald-500"
            />
            <span className="text-zinc-500 text-xs">-</span>
            <input
              type="date"
              value={customRange.to}
              onChange={(e) => setCustomRange(prev => ({ ...prev, to: e.target.value }))}
              className="px-2 py-1 text-xs bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-750 border border-zinc-700 text-zinc-300 font-bold rounded-lg text-xs transition cursor-pointer"
            >
              Apply
            </button>
            {(fromDate || toDate) && (
              <button
                type="button"
                onClick={() => {
                  setSelectedMonth("");
                  setCustomRange({ from: "", to: "" });
                  setFromDate("");
                  setToDate("");
                }}
                className="px-2.5 py-1 text-zinc-500 hover:text-zinc-350 text-xs font-semibold"
              >
                Reset
              </button>
            )}
          </form>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="max-w-7xl mx-auto w-full flex-1 flex flex-col lg:flex-row gap-8">
        
        {/* Navigation Tabs (Sidebar Layout) */}
        <aside className="w-full lg:w-64 flex-shrink-0 flex flex-row lg:flex-col gap-1.5 overflow-x-auto lg:overflow-x-visible pb-3 lg:pb-0 border-b lg:border-b-0 border-zinc-900 self-start">
          <button
            onClick={() => setActiveTab("overview")}
            className={`w-auto lg:w-full px-4 py-3 rounded-xl transition flex items-center justify-center lg:justify-start gap-2.5 text-xs font-bold whitespace-nowrap cursor-pointer ${
              activeTab === "overview"
                ? "bg-emerald-500 text-zinc-950 font-extrabold shadow-md shadow-emerald-500/10"
                : "bg-zinc-900/10 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
            }`}
          >
            <LayoutDashboard className="w-4 h-4 flex-shrink-0" />
            <span>Overview</span>
          </button>

          <button
            onClick={() => setActiveTab("categories")}
            className={`w-auto lg:w-full px-4 py-3 rounded-xl transition flex items-center justify-center lg:justify-start gap-2.5 text-xs font-bold whitespace-nowrap cursor-pointer ${
              activeTab === "categories"
                ? "bg-emerald-500 text-zinc-950 font-extrabold shadow-md shadow-emerald-500/10"
                : "bg-zinc-900/10 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
            }`}
          >
            <PieChart className="w-4 h-4 flex-shrink-0" />
            <span>Categories</span>
          </button>

          <button
            onClick={() => setActiveTab("transactions")}
            className={`w-auto lg:w-full px-4 py-3 rounded-xl transition flex items-center justify-center lg:justify-start gap-2.5 text-xs font-bold whitespace-nowrap cursor-pointer ${
              activeTab === "transactions"
                ? "bg-emerald-500 text-zinc-950 font-extrabold shadow-md shadow-emerald-500/10"
                : "bg-zinc-900/10 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
            }`}
          >
            <ListFilter className="w-4 h-4 flex-shrink-0" />
            <span>Transactions</span>
          </button>

          <button
            onClick={() => setActiveTab("recurring")}
            className={`w-auto lg:w-full px-4 py-3 rounded-xl transition flex items-center justify-center lg:justify-start gap-2.5 text-xs font-bold whitespace-nowrap cursor-pointer ${
              activeTab === "recurring"
                ? "bg-emerald-500 text-zinc-950 font-extrabold shadow-md shadow-emerald-500/10"
                : "bg-zinc-900/10 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
            }`}
          >
            <Repeat className="w-4 h-4 flex-shrink-0" />
            <span>Recurring</span>
          </button>

          <button
            onClick={() => setActiveTab("insights")}
            className={`w-auto lg:w-full px-4 py-3 rounded-xl transition flex items-center justify-center lg:justify-start gap-2.5 text-xs font-bold whitespace-nowrap cursor-pointer ${
              activeTab === "insights"
                ? "bg-emerald-500 text-zinc-950 font-extrabold shadow-md shadow-emerald-500/10"
                : "bg-zinc-900/10 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800"
            }`}
          >
            <Sparkles className="w-4 h-4 flex-shrink-0" />
            <span>Insights</span>
          </button>
        </aside>

        {/* Tab Content Area */}
        <section className="flex-1 flex flex-col gap-6 min-w-0">
          {activeTab === "overview" && summary && (
            <div className="flex flex-col gap-6 w-full">
              <SummaryCards summary={summary} />
              
              {/* Preview of Insights */}
              <div className="w-full mt-2">
                <InsightCards insights={insights.slice(0, 2)} />
              </div>
            </div>
          )}

          {activeTab === "categories" && summary && (
            <CategoryChart categories={summary.topCategories} />
          )}

          {activeTab === "transactions" && (
            <TransactionTable 
              sessionId={sessionId} 
              onRefreshData={handleRefresh} 
              fromDate={fromDate}
              toDate={toDate}
            />
          )}

          {activeTab === "recurring" && (
            <RecurringList sessionId={sessionId} />
          )}

          {activeTab === "insights" && (
            <InsightCards insights={insights} />
          )}
        </section>
      </div>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full text-center border-t border-zinc-900/80 pt-6 mt-8 text-[10px] text-zinc-500">
        RupeeRadar live dashboard view. This session expires automatically 24h after initialization.
      </footer>
    </div>
  );
}
