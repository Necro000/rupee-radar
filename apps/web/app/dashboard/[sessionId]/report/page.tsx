"use client";

import React, { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Printer, ArrowLeft, RefreshCw, AlertCircle, FileText } from "lucide-react";
import { api, SummaryResponse, Insight, Transaction } from "../../../../lib/api";

export default function ReportPage({ params }: { params: Promise<{ sessionId: string }> }) {
  const router = useRouter();
  const { sessionId } = use(params);

  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReportData();
  }, [sessionId]);

  const loadReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch metrics, insights and all transactions in parallel
      const [summaryRes, insightsRes, txsRes] = await Promise.all([
        api.getSummary(sessionId),
        api.getInsights(sessionId),
        api.getTransactions(sessionId, 1, 500) // Fetch up to 500 transactions for the ledger
      ]);

      setSummary(summaryRes);
      setInsights(insightsRes);
      setTransactions(txsRes.transactions);
    } catch (e: any) {
      console.error(e);
      setError(e.message || "Failed to load statement report. The session may have expired.");
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = () => {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.open(`${API_BASE_URL}/api/v1/sessions/${sessionId}/report?format=pdf`, "_blank");
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(val);
  };

  const formatTxCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2
    }).format(val);
  };

  if (loading) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col items-center justify-center min-h-screen text-zinc-400 print:hidden">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 border-4 border-emerald-500/25 border-t-emerald-400 rounded-full animate-spin"></div>
          <span className="text-sm font-semibold tracking-wider uppercase text-zinc-500">Compiling Printable Report...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="flex-1 bg-zinc-950 flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8 print:hidden">
        <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-6 text-center">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-bold text-zinc-100">Report Compilation Failed</h3>
          <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{error}</p>
          <button
            onClick={() => router.push(`/dashboard/${sessionId}`)}
            className="w-full mt-6 py-2.5 bg-zinc-850 hover:bg-zinc-800 text-zinc-200 border border-zinc-700 font-bold rounded-xl text-xs flex items-center justify-center gap-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans p-6 sm:p-12 print:p-0">
      <div className="max-w-4xl mx-auto flex flex-col gap-8">
        
        {/* Navigation / Control Bar (Hidden on Print) */}
        <div className="no-print flex items-center justify-between bg-zinc-100 border border-zinc-200 rounded-xl p-4 print:hidden">
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push(`/dashboard/${sessionId}`)}
              className="p-2 hover:bg-zinc-200 rounded-lg text-zinc-650 hover:text-zinc-900 transition flex items-center gap-1.5 text-xs font-bold"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Dashboard</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadPDF}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 font-bold rounded-lg text-xs flex items-center gap-2 transition cursor-pointer"
            >
              <FileText className="w-4 h-4 text-emerald-400" />
              <span>Download PDF (Backend)</span>
            </button>

            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-zinc-950 font-extrabold rounded-lg text-xs flex items-center gap-2 shadow-md transition cursor-pointer"
            >
              <Printer className="w-4 h-4" />
              <span>Save PDF / Print</span>
            </button>
          </div>
        </div>

        {/* Report Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b-2 border-zinc-200 pb-6 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-emerald-600 flex items-center justify-center font-bold text-white text-lg">
                ₹
              </div>
              <h1 className="text-xl font-black tracking-tight text-zinc-950">RupeeRadar</h1>
            </div>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mt-1">
              Personal Statement Analysis Report
            </p>
          </div>
          
          <div className="text-left sm:text-right text-xs text-zinc-500 font-medium space-y-1">
            <div><strong>Session Ref:</strong> {sessionId}</div>
            <div><strong>Report Type:</strong> Audit Snapshot</div>
            <div><strong>Generated At:</strong> {new Date().toLocaleDateString("en-IN")}</div>
          </div>
        </div>

        {/* Core KPI Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <div className="border border-zinc-200 rounded-xl p-4 bg-zinc-50">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Total Income</span>
            <h3 className="text-lg font-black text-emerald-650 mt-1">{formatCurrency(summary.income)}</h3>
          </div>
          <div className="border border-zinc-200 rounded-xl p-4 bg-zinc-50">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Total Spend</span>
            <h3 className="text-lg font-black text-rose-650 mt-1">{formatCurrency(summary.spend)}</h3>
          </div>
          <div className="border border-zinc-200 rounded-xl p-4 bg-zinc-50">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Net Savings</span>
            <h3 className={`text-lg font-black mt-1 ${summary.savings >= 0 ? "text-cyan-650" : "text-rose-650"}`}>
              {formatCurrency(summary.savings)}
            </h3>
          </div>
          <div className="border border-zinc-200 rounded-xl p-4 bg-zinc-50">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Savings Rate</span>
            <h3 className="text-lg font-black text-zinc-800 mt-1">{summary.savingsRate}%</h3>
          </div>
          <div className="border border-zinc-200 rounded-xl p-4 bg-zinc-50 col-span-2 sm:col-span-1">
            <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Recurring Total</span>
            <h3 className="text-lg font-black text-zinc-800 mt-1">{formatCurrency(summary.recurringTotal)}</h3>
          </div>
        </div>

        {/* Category spends & insights row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          {/* Category List */}
          <div className="flex flex-col gap-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider border-b border-zinc-200 pb-2 text-zinc-800">
              Spend by Category
            </h3>
            
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-zinc-250 text-zinc-500 font-bold uppercase text-[10px]">
                  <th className="py-2.5">Category</th>
                  <th className="py-2.5 text-right">Amount</th>
                  <th className="py-2.5 text-right">% of Spend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-150">
                {summary.topCategories.map((cat, i) => (
                  <tr key={i}>
                    <td className="py-2.5 font-semibold text-zinc-800">{cat.category}</td>
                    <td className="py-2.5 text-right font-medium text-zinc-700">{formatCurrency(cat.amount)}</td>
                    <td className="py-2.5 text-right font-extrabold text-emerald-600">{cat.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {summary.biggestTransaction && (
              <div className="border border-zinc-200 rounded-xl p-4 mt-2 bg-zinc-50">
                <span className="text-[9px] uppercase tracking-wider font-extrabold text-zinc-400">Largest Single Expense</span>
                <h4 className="text-xs font-bold text-zinc-800 mt-1 truncate">{summary.biggestTransaction.description}</h4>
                <div className="flex gap-2 items-center text-[10px] text-zinc-500 mt-1">
                  <span>Date: {summary.biggestTransaction.date}</span> |
                  <span>Category: {summary.biggestTransaction.category}</span>
                </div>
                <div className="text-lg font-black text-rose-650 mt-2">
                  {formatCurrency(Math.abs(summary.biggestTransaction.amount))}
                </div>
              </div>
            )}
          </div>

          {/* Behavior Insights */}
          <div className="flex flex-col gap-4">
            <h3 className="text-sm font-extrabold uppercase tracking-wider border-b border-zinc-200 pb-2 text-zinc-800">
              Behavioral Insights
            </h3>
            
            <div className="flex flex-col gap-3">
              {insights.map((ins, i) => {
                const borderClass = ins.relevance >= 0.85
                  ? "border-red-500/30 border-l-red-500" 
                  : ins.id === "insight_savings_healthy"
                    ? "border-emerald-500/30 border-l-emerald-500"
                    : "border-zinc-200 border-l-zinc-400";

                return (
                  <div 
                    key={ins.id || i} 
                    className={`border border-l-4 rounded-xl p-4 bg-zinc-50/50 flex flex-col gap-1 ${borderClass}`}
                  >
                    <div className="flex justify-between items-center text-[9px] font-extrabold text-zinc-400 uppercase tracking-widest">
                      <span>{ins.type.replace("_", " ")}</span>
                      <span>Relevance: {ins.relevance.toFixed(2)}</span>
                    </div>
                    <h4 className="text-xs font-extrabold text-zinc-900 mt-1">{ins.title}</h4>
                    <p className="text-[11px] text-zinc-650 leading-relaxed mt-0.5">{ins.text}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Page Break for print */}
        <div className="page-break" style={{ pageBreakBefore: "always" }}></div>

        {/* Transaction Ledger Table */}
        <div className="flex flex-col gap-4 mt-6">
          <h3 className="text-sm font-extrabold uppercase tracking-wider border-b border-zinc-200 pb-2 text-zinc-800">
            Statement ledger
          </h3>
          
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-zinc-250 text-zinc-500 font-bold uppercase text-[10px]">
                <th className="py-2.5">Date</th>
                <th className="py-2.5">Description</th>
                <th className="py-2.5">Category</th>
                <th className="py-2.5 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-150">
              {transactions.map((tx) => {
                const isDebit = tx.type === "debit";
                return (
                  <tr key={tx.id} className="hover:bg-zinc-50/30 transition">
                    <td className="py-2.5 whitespace-nowrap text-zinc-500 font-mono text-[10px]">{tx.date}</td>
                    <td className="py-2.5 pr-4">
                      <div className="font-semibold text-zinc-850">{tx.cleanDescription}</div>
                      <div className="text-[9px] text-zinc-400 font-mono mt-0.5">{tx.rawDescription}</div>
                    </td>
                    <td className="py-2.5 whitespace-nowrap">
                      <span className="inline-flex px-2 py-0.5 bg-zinc-100 border border-zinc-200 rounded text-[9px] font-bold text-zinc-600">
                        {tx.category}
                      </span>
                    </td>
                    <td className={`py-2.5 text-right font-bold whitespace-nowrap ${isDebit ? "text-rose-650" : "text-emerald-650"}`}>
                      {isDebit ? "-" : ""}{formatTxCurrency(Math.abs(tx.amount))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

      </div>

      {/* Global CSS for hiding print controls */}
      <style jsx global>{`
        @media print {
          .no-print {
            display: none !important;
          }
          body {
            background-color: white !important;
            color: black !important;
            padding: 0 !important;
          }
          .page-break {
            page-break-before: always !important;
          }
        }
      `}</style>
    </div>
  );
}
