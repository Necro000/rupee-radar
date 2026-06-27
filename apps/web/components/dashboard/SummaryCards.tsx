"use client";

import React from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Percent, 
  Repeat, 
  AlertTriangle,
  ArrowRight,
  TrendingDown as DecreaseIcon 
} from "lucide-react";
import { SummaryResponse } from "../../lib/api";

interface SummaryCardsProps {
  summary: SummaryResponse;
}

export default function SummaryCards({ summary }: SummaryCardsProps) {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(val);
  };

  const {
    income,
    spend,
    savings,
    savingsRate,
    recurringTotal,
    biggestTransaction
  } = summary;

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* 5-Card Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Income Card */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Total Income</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <h3 className="text-2xl font-extrabold text-zinc-100">{formatCurrency(income)}</h3>
            <p className="text-[10px] text-zinc-500 mt-1">Total statement credits</p>
          </div>
        </div>

        {/* Spend Card */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Total Spend</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <h3 className="text-2xl font-extrabold text-zinc-100">{formatCurrency(spend)}</h3>
            <p className="text-[10px] text-zinc-500 mt-1">Total statement debits</p>
          </div>
        </div>

        {/* Savings Card */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Net Savings</span>
            <div className={`p-2 rounded-xl ${savings >= 0 ? 'bg-cyan-500/10 text-cyan-400' : 'bg-red-500/10 text-red-400'}`}>
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <h3 className={`text-2xl font-extrabold ${savings >= 0 ? 'text-zinc-100' : 'text-red-400'}`}>
              {formatCurrency(savings)}
            </h3>
            <p className="text-[10px] text-zinc-500 mt-1">Statement balance delta</p>
          </div>
        </div>

        {/* Savings Rate Card */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Savings Rate</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Percent className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <h3 className="text-2xl font-extrabold text-zinc-100">{savingsRate}%</h3>
            <p className="text-[10px] text-zinc-500 mt-1">Target: 20% benchmark</p>
          </div>
        </div>

        {/* Recurring Card */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-5 backdrop-blur-md relative overflow-hidden flex flex-col justify-between min-h-[120px]">
          <div className="flex justify-between items-start">
            <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wider">Recurring Total</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Repeat className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <h3 className="text-2xl font-extrabold text-zinc-100">{formatCurrency(recurringTotal)}</h3>
            <p className="text-[10px] text-zinc-500 mt-1">Monthly recurring burden</p>
          </div>
        </div>
      </div>

      {/* Biggest Transaction & Detailed Overview Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Biggest Transaction card */}
        <div className="lg:col-span-2 bg-gradient-to-r from-zinc-900/50 to-zinc-900/20 border border-zinc-800 rounded-2xl p-6 backdrop-blur-md flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <h4 className="text-sm font-bold text-zinc-200 uppercase tracking-wider">Largest Single Expense</h4>
            </div>
            {biggestTransaction ? (
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                <div>
                  <h3 className="text-lg font-bold text-zinc-100 truncate max-w-md">
                    {biggestTransaction.description}
                  </h3>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-medium">
                      {biggestTransaction.date}
                    </span>
                    {biggestTransaction.merchant && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-medium">
                        {biggestTransaction.merchant}
                      </span>
                    )}
                    <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 font-semibold uppercase tracking-wider">
                      {biggestTransaction.category}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-extrabold text-rose-400">
                    {formatCurrency(Math.abs(biggestTransaction.amount))}
                  </span>
                  <p className="text-[10px] text-zinc-500 mt-1">
                    {spend > 0 ? ((Math.abs(biggestTransaction.amount) / spend) * 100).toFixed(1) : 0}% of total spend
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-4 text-center text-zinc-500 text-sm">
                No debit transactions found in this period.
              </div>
            )}
          </div>
        </div>

        {/* Balance Ratio Summary */}
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 backdrop-blur-md flex flex-col justify-between">
          <h4 className="text-sm font-bold text-zinc-300 mb-4">Statement Overview</h4>
          
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs text-zinc-400 mb-1">
                <span>Spend vs Income Ratio</span>
                <span className="font-semibold">{income > 0 ? ((spend / income) * 100).toFixed(0) : 100}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-rose-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${income > 0 ? Math.min(100, (spend / income) * 100) : 100}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs text-zinc-400 mb-1">
                <span>Recurring Commitments Ratio</span>
                <span className="font-semibold">{income > 0 ? ((recurringTotal / income) * 100).toFixed(0) : 0}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                <div 
                  className="bg-amber-500 h-full rounded-full transition-all duration-500" 
                  style={{ width: `${income > 0 ? Math.min(100, (recurringTotal / income) * 100) : 0}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
