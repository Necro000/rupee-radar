"use client";

import React, { useState, useEffect } from "react";
import { Search, ChevronLeft, ChevronRight, Check, AlertCircle, Sparkles } from "lucide-react";
import { api, Transaction } from "../../lib/api";

interface TransactionTableProps {
  sessionId: string;
  onRefreshData: () => void;
  fromDate?: string;
  toDate?: string;
}

const CATEGORIES = [
  "Food",
  "Travel",
  "Shopping",
  "Bills",
  "EMI",
  "Subscriptions",
  "Salary",
  "Rent",
  "Investments",
  "Other"
];

const CATEGORY_COLORS: Record<string, string> = {
  "Food": "bg-amber-500/10 text-amber-400 border-amber-500/20",
  "Travel": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "Shopping": "bg-pink-500/10 text-pink-400 border-pink-500/20",
  "Bills": "bg-red-500/10 text-red-400 border-red-500/20",
  "EMI": "bg-purple-500/10 text-purple-400 border-purple-500/20",
  "Subscriptions": "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  "Salary": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  "Rent": "bg-orange-500/10 text-orange-400 border-orange-500/20",
  "Investments": "bg-teal-500/10 text-teal-400 border-teal-500/20",
  "Other": "bg-zinc-500/10 text-zinc-400 border-zinc-500/20"
};

export default function TransactionTable({ sessionId, onRefreshData, fromDate, toDate }: TransactionTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Track overrides in progress
  const [overrideTargetId, setOverrideTargetId] = useState<string | null>(null);
  const [overrideMessage, setOverrideMessage] = useState<string | null>(null);

  useEffect(() => {
    loadTransactions();
  }, [sessionId, page, selectedCategory, fromDate, toDate]);

  const loadTransactions = async () => {
    setLoading(true);
    try {
      const res = await api.getTransactions(
        sessionId,
        page,
        10, // Limit
        selectedCategory || undefined,
        search || undefined,
        fromDate || undefined,
        toDate || undefined
      );
      setTransactions(res.transactions);
      setTotalItems(res.total);
      setTotalPages(res.pages || 1);
    } catch (e) {
      console.error("Failed to load transactions", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadTransactions();
  };

  const handleCategoryOverride = async (txId: string, newCategory: string) => {
    setOverrideTargetId(txId);
    setOverrideMessage(null);
    try {
      const res = await api.overrideCategory(sessionId, txId, newCategory);

      setOverrideMessage(res.message || "Category overridden successfully.");
      
      // Reload current table state & update parent summary
      loadTransactions();
      onRefreshData();
      
      setTimeout(() => setOverrideMessage(null), 3000);
    } catch (e: any) {
      console.error(e);
      alert(`Override failed: ${e.message || e}`);
    } finally {
      setOverrideTargetId(null);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2
    }).format(val);
  };

  return (
    <div className="w-full flex flex-col gap-5 bg-zinc-900/30 border border-zinc-800/85 rounded-2xl p-6 backdrop-blur-md">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-zinc-100">Transaction History</h3>
          <p className="text-xs text-zinc-400">View and refine statements records</p>
        </div>

        {/* Filters */}
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          {/* Category Dropdown Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 text-xs font-semibold bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-300 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat, idx) => (
              <option key={idx} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Search Input */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search descriptions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 text-xs bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition min-w-[200px]"
            />
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            {search && (
              <button
                type="button"
                onClick={() => {
                  setSearch("");
                  setPage(1);
                  setTimeout(loadTransactions, 50);
                }}
                className="text-[10px] text-zinc-500 hover:text-zinc-300 absolute right-3 top-1/2 -translate-y-1/2 font-semibold"
              >
                Clear
              </button>
            )}
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-emerald-500 text-zinc-950 hover:bg-emerald-400 font-bold rounded-xl text-xs transition active:scale-95 cursor-pointer"
          >
            Apply
          </button>
        </form>
      </div>

      {/* Override Alert Message */}
      {overrideMessage && (
        <div className="w-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl p-3 flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 animate-bounce" />
          <span>{overrideMessage}</span>
        </div>
      )}

      {/* Table Container */}
      <div className="overflow-x-auto border border-zinc-850 rounded-xl">
        <table className="w-full border-collapse text-left text-xs text-zinc-300">
          <thead className="bg-zinc-950/80 text-zinc-400 border-b border-zinc-850 uppercase font-bold tracking-wider">
            <tr>
              <th className="p-4">Date</th>
              <th className="p-4">Merchant / Description</th>
              <th className="p-4">Category</th>
              <th className="p-4 text-right">Amount</th>
              <th className="p-4 text-center">Correct Category</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900 bg-zinc-950/10">
            {loading ? (
              <tr>
                <td colSpan={5} className="p-10 text-center text-zinc-500">
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-6 w-6 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                    <span>Loading transactions...</span>
                  </div>
                </td>
              </tr>
            ) : transactions.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-10 text-center text-zinc-500">
                  No transaction records matched the filters.
                </td>
              </tr>
            ) : (
              transactions.map((tx) => {
                const isDebit = tx.type === "debit";
                return (
                  <tr key={tx.id} className="hover:bg-zinc-900/30 transition">
                    {/* Date */}
                    <td className="p-4 whitespace-nowrap text-zinc-450 font-medium">{tx.date}</td>
                    
                    {/* Description */}
                    <td className="p-4 max-w-sm sm:max-w-md">
                      <div className="truncate font-semibold text-zinc-200" title={tx.cleanDescription}>
                        {tx.cleanDescription}
                      </div>
                      <div className="truncate text-[10px] text-zinc-500 font-mono mt-0.5" title={tx.rawDescription}>
                        {tx.rawDescription}
                      </div>
                    </td>

                    {/* Category Badge */}
                    <td className="p-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${CATEGORY_COLORS[tx.category] || CATEGORY_COLORS["Other"]} ${tx.categorySource !== "user" && tx.categoryConfidence < 0.8 ? 'ring-1 ring-amber-500/40 border-amber-500/30' : ''}`}>
                          {tx.category}
                          {tx.categorySource === "user" && (
                            <span className="ml-1 text-[8px] bg-emerald-500/20 text-emerald-350 px-1 rounded-sm uppercase tracking-wider font-bold">
                              User
                            </span>
                          )}
                        </span>
                        {tx.categorySource !== "user" && tx.categoryConfidence < 0.8 && (
                          <span title={`Low confidence classification (${Math.round(tx.categoryConfidence * 100)}%). Select a correct category on the right to train a new custom matching rule.`}>
                            <AlertCircle 
                              className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 animate-pulse cursor-help" 
                            />
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Amount */}
                    <td className={`p-4 text-right font-bold text-sm whitespace-nowrap ${isDebit ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {isDebit ? "-" : ""}{formatCurrency(Math.abs(tx.amount))}
                    </td>

                    {/* Category Override Control */}
                    <td className="p-4 text-center whitespace-nowrap">
                      {overrideTargetId === tx.id ? (
                        <div className="h-4 w-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
                      ) : (
                        <select
                          value={tx.category}
                          onChange={(e) => handleCategoryOverride(tx.id, e.target.value)}
                          className="px-2 py-1 text-[10px] font-bold bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-md text-zinc-400 focus:outline-none focus:border-emerald-500 transition cursor-pointer"
                        >
                          {CATEGORIES.map((cat, idx) => (
                            <option key={idx} value={cat}>{cat}</option>
                          ))}
                        </select>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-zinc-900 pt-4 mt-2">
          <span className="text-[10px] text-zinc-500 font-semibold">
            Showing Page {page} of {totalPages} ({totalItems} transactions total)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200 transition disabled:opacity-30 disabled:cursor-not-allowed bg-zinc-950"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200 transition disabled:opacity-30 disabled:cursor-not-allowed bg-zinc-950"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
