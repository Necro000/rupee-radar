"use client";

import React, { useState, useEffect } from "react";
import { 
  ChevronDown, 
  ChevronUp, 
  Repeat, 
  Calendar, 
  CreditCard,
  Briefcase,
  HelpCircle,
  Activity
} from "lucide-react";
import { api, RecurringGroup } from "../../lib/api";

interface RecurringListProps {
  sessionId: string;
}

const FREQUENCY_LABELS: Record<string, string> = {
  "weekly": "Weekly",
  "monthly": "Monthly",
  "quarterly": "Quarterly",
  "yearly": "Yearly"
};

const TYPE_ICONS: Record<string, React.ReactNode> = {
  "subscription": <CreditCard className="w-4 h-4 text-cyan-400" />,
  "emi": <Activity className="w-4 h-4 text-purple-400" />,
  "rent": <Briefcase className="w-4 h-4 text-orange-400" />,
  "sip": <Repeat className="w-4 h-4 text-emerald-400" />,
  "insurance": <Calendar className="w-4 h-4 text-rose-400" />,
  "other": <HelpCircle className="w-4 h-4 text-zinc-400" />
};

export default function RecurringList({ sessionId }: RecurringListProps) {
  const [groups, setGroups] = useState<RecurringGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedGroupIds, setExpandedGroupIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadRecurringGroups();
  }, [sessionId]);

  const loadRecurringGroups = async () => {
    setLoading(true);
    try {
      const data = await api.getRecurring(sessionId);
      setGroups(data);
    } catch (e) {
      console.error("Failed to load recurring groups", e);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (groupId: string) => {
    const next = new Set(expandedGroupIds);
    if (next.has(groupId)) {
      next.delete(groupId);
    } else {
      next.add(groupId);
    }
    setExpandedGroupIds(next);
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
      <div className="w-full bg-zinc-900/30 border border-zinc-800 rounded-2xl p-10 flex flex-col items-center justify-center gap-2 text-zinc-500 backdrop-blur-md">
        <div className="h-6 w-6 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
        <span>Analyzing recurring payments...</span>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="w-full bg-zinc-900/30 border border-zinc-800 rounded-2xl p-10 text-center text-zinc-500 backdrop-blur-md flex flex-col items-center gap-3">
        <div className="p-3 rounded-2xl bg-zinc-850 text-zinc-400">
          <Repeat className="w-6 h-6" />
        </div>
        <div>
          <h4 className="text-zinc-350 font-bold">No recurring payments identified</h4>
          <p className="text-xs text-zinc-500 max-w-sm mt-1 mx-auto">
            The database could not find recurring transaction patterns (e.g. at least 2 matching transactions with identical amounts at equal intervals).
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-5 bg-zinc-900/30 border border-zinc-800/85 rounded-2xl p-6 backdrop-blur-md">
      <div>
        <h3 className="text-lg font-bold text-zinc-100">Recurring Commitments</h3>
        <p className="text-xs text-zinc-400">Detected subscriptions, insurance premium payments, rent, and EMIs</p>
      </div>

      <div className="flex flex-col gap-4">
        {groups.map((group) => {
          const isExpanded = expandedGroupIds.has(group.groupId);
          return (
            <div 
              key={group.groupId} 
              className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-950/20 hover:border-zinc-700/80 transition"
            >
              {/* Summary Row */}
              <div 
                onClick={() => toggleExpand(group.groupId)}
                className="p-4 flex items-center justify-between gap-4 cursor-pointer select-none bg-zinc-900/10 hover:bg-zinc-900/30 transition"
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  {/* Icon depending on type */}
                  <div className="p-2.5 rounded-xl bg-zinc-900 border border-zinc-850 flex-shrink-0 flex items-center justify-center">
                    {TYPE_ICONS[group.type] || TYPE_ICONS["other"]}
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-bold text-zinc-200 truncate pr-4 text-sm sm:text-base">
                      {group.merchant || group.description}
                    </h4>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-400">
                        {FREQUENCY_LABELS[group.frequency] || group.frequency}
                      </span>
                      <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-md bg-zinc-900 text-zinc-500">
                        {group.type}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-medium">
                        ({group.transactions.length} payments)
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-base sm:text-lg font-black text-zinc-100">
                      {formatCurrency(group.amount)}
                    </span>
                    <p className="text-[9px] text-zinc-500 font-medium uppercase tracking-wider mt-0.5">Average payment</p>
                  </div>
                  <div className="text-zinc-500">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>
              </div>

              {/* Collapsible Details */}
              {isExpanded && (
                <div className="border-t border-zinc-900 bg-zinc-950/40 p-4">
                  <div className="text-[10px] font-bold text-zinc-450 uppercase tracking-wider mb-2.5">
                    Individual Payments History
                  </div>
                  <div className="space-y-2">
                    {group.transactions.map((tx) => (
                      <div 
                        key={tx.id} 
                        className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/35 border border-zinc-900 text-xs hover:bg-zinc-900/60 transition"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-zinc-500 font-mono text-[10px]">
                            {tx.date}
                          </span>
                          <span className="text-zinc-300 font-medium truncate max-w-sm sm:max-w-md">
                            {tx.cleanDescription}
                          </span>
                        </div>
                        <span className="font-bold text-rose-400">
                          -{formatTxCurrency(Math.abs(tx.amount))}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
