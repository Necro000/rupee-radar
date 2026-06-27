"use client";

import React from "react";
import { 
  Sparkles, 
  Lightbulb, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Heart,
  Wallet,
  PieChart,
  Repeat
} from "lucide-react";
import { Insight } from "../../lib/api";

interface InsightCardsProps {
  insights: Insight[];
}

export default function InsightCards({ insights }: InsightCardsProps) {
  const getInsightStyle = (insight: Insight) => {
    const type = insight.type;
    const relevance = insight.relevance;

    // High relevance items (>= 0.8) are alerts or high-priority warnings
    if (relevance >= 0.85) {
      return {
        bg: "bg-red-500/5 hover:bg-red-500/10 border-red-500/20 hover:border-red-500/40",
        badge: "bg-red-500/10 text-red-400 border-red-500/20",
        iconBg: "bg-red-500/10 text-red-400 border-red-500/25",
        icon: <AlertTriangle className="w-5 h-5" />,
        priorityLabel: "Critical Action Item"
      };
    }

    switch (type) {
      case "savings_rate":
        if (insight.id === "insight_savings_healthy") {
          return {
            bg: "bg-emerald-500/5 hover:bg-emerald-500/10 border-emerald-500/20 hover:border-emerald-500/45",
            badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            iconBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
            icon: <Wallet className="w-5 h-5" />,
            priorityLabel: "Excellent Performance"
          };
        }
        return {
          bg: "bg-amber-500/5 hover:bg-amber-500/10 border-amber-500/20 hover:border-amber-500/40",
          badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
          iconBg: "bg-amber-500/10 text-amber-400 border-amber-500/25",
          icon: <Wallet className="w-5 h-5" />,
          priorityLabel: "Recommendation"
        };
      
      case "top_category":
        return {
          bg: "bg-blue-500/5 hover:bg-blue-500/10 border-blue-500/20 hover:border-blue-500/40",
          badge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
          iconBg: "bg-blue-500/10 text-blue-400 border-blue-500/25",
          icon: <PieChart className="w-5 h-5" />,
          priorityLabel: "Spend Highlight"
        };

      case "biggest_purchase":
        return {
          bg: "bg-purple-500/5 hover:bg-purple-500/10 border-purple-500/20 hover:border-purple-500/40",
          badge: "bg-purple-500/10 text-purple-400 border-purple-500/20",
          iconBg: "bg-purple-500/10 text-purple-400 border-purple-500/25",
          icon: <AlertTriangle className="w-5 h-5" />,
          priorityLabel: "Significant Outflow"
        };

      case "recurring_burden":
        return {
          bg: "bg-orange-500/5 hover:bg-orange-500/10 border-orange-500/20 hover:border-orange-500/40",
          badge: "bg-orange-500/10 text-orange-400 border-orange-500/20",
          iconBg: "bg-orange-500/10 text-orange-400 border-orange-500/25",
          icon: <Repeat className="w-5 h-5" />,
          priorityLabel: "Fixed Commitment"
        };

      case "month_comparison":
        const titleLower = insight.title.toLowerCase();
        const isUp = titleLower.includes("increase") || titleLower.includes("upward");
        return {
          bg: isUp 
            ? "bg-red-500/5 hover:bg-red-500/10 border-red-500/15 hover:border-red-500/35"
            : "bg-emerald-500/5 hover:bg-emerald-500/10 border-emerald-500/15 hover:border-emerald-500/35",
          badge: isUp ? "bg-red-500/10 text-red-400 border-red-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
          iconBg: isUp ? "bg-red-500/10 text-red-400 border-red-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
          icon: isUp ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />,
          priorityLabel: "Month-on-Month Trend"
        };

      case "budget_tip":
      default:
        return {
          bg: "bg-zinc-900/40 hover:bg-zinc-900/60 border-zinc-800 hover:border-zinc-700",
          badge: "bg-zinc-800 text-zinc-400 border-zinc-750",
          iconBg: "bg-zinc-800/80 text-zinc-400 border-zinc-750",
          icon: <Lightbulb className="w-5 h-5 text-amber-400" />,
          priorityLabel: "Budgeting Principle"
        };
    }
  };

  if (!insights || insights.length === 0) {
    return (
      <div className="w-full bg-zinc-900/40 border border-zinc-800 rounded-2xl p-10 flex items-center justify-center text-zinc-500 backdrop-blur-md">
        No financial insights generated yet.
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-6 bg-zinc-900/30 border border-zinc-800/85 rounded-2xl p-6 backdrop-blur-md">
      <div>
        <h3 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-emerald-400 animate-pulse" />
          <span>Personalized Financial Insights</span>
        </h3>
        <p className="text-xs text-zinc-400">Behavioral reviews, optimization proposals, and recommendations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, idx) => {
          const style = getInsightStyle(insight);
          return (
            <div 
              key={insight.id || idx} 
              className={`border rounded-2xl p-5 flex gap-4 transition duration-300 backdrop-blur-sm group ${style.bg}`}
            >
              {/* Icon Container */}
              <div className={`p-3 rounded-xl border flex-shrink-0 flex items-center justify-center self-start h-11 w-11 transition group-hover:scale-105 duration-300 ${style.iconBg}`}>
                {style.icon}
              </div>

              {/* Text Area */}
              <div className="flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 border text-[9px] uppercase tracking-wider font-extrabold rounded-md ${style.badge}`}>
                      {style.priorityLabel}
                    </span>
                    {insight.relevance > 0 && (
                      <span className="text-[9px] text-zinc-500 font-semibold">
                        Score: {insight.relevance.toFixed(2)}
                      </span>
                    )}
                  </div>
                  
                  <h4 className="text-sm font-extrabold text-zinc-250 mt-2 group-hover:text-zinc-100 transition">
                    {insight.title}
                  </h4>
                  
                  <p className="text-xs text-zinc-450 leading-relaxed mt-1.5 group-hover:text-zinc-350 transition">
                    {insight.text}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
