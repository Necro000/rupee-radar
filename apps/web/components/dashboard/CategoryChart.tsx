"use client";

import React, { useState } from "react";
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts";
import { PieChart as PieIcon, BarChart3 as BarIcon, Grid as GridIcon } from "lucide-react";

interface CategorySpend {
  category: string;
  amount: number;
  percentage: number;
}

interface CategoryChartProps {
  categories: CategorySpend[];
}

const CATEGORY_COLORS: Record<string, string> = {
  "Food": "#F59E0B",          // Amber
  "Travel": "#3B82F6",        // Blue
  "Shopping": "#EC4899",      // Pink
  "Bills": "#EF4444",         // Red
  "EMI": "#8B5CF6",           // Purple
  "Subscriptions": "#06B6D4", // Cyan
  "Salary": "#10B981",        // Emerald
  "Rent": "#F97316",          // Orange
  "Investments": "#14B8A6",   // Teal
  "Other": "#6B7280"          // Gray
};

const DEFAULT_COLOR = "#71717A";

export default function CategoryChart({ categories }: CategoryChartProps) {
  const [viewMode, setViewMode] = useState<"pie" | "bar" | "grid">("pie");

  if (!categories || categories.length === 0) {
    return (
      <div className="w-full bg-zinc-900/40 border border-zinc-800 rounded-2xl p-10 flex items-center justify-center text-zinc-500 backdrop-blur-md">
        No expense transactions available to generate charts.
      </div>
    );
  }

  // Format charts tooltip values
  const formatTooltipValue = (value: any) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(Number(value) || 0);
  };

  const chartData = categories.map(cat => ({
    name: cat.category,
    value: cat.amount,
    percentage: cat.percentage,
    fill: CATEGORY_COLORS[cat.category] || DEFAULT_COLOR
  }));

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="w-full flex flex-col gap-6 bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md">
      {/* Header and Toggle Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-zinc-100">Spend Distribution</h3>
          <p className="text-xs text-zinc-400">Expense breakdown by category</p>
        </div>

        <div className="flex items-center self-start sm:self-center bg-zinc-950 p-1 rounded-xl border border-zinc-850">
          <button
            onClick={() => setViewMode("pie")}
            className={`p-2 rounded-lg transition flex items-center gap-1.5 text-xs font-semibold ${
              viewMode === "pie"
                ? "bg-zinc-800 text-emerald-400"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <PieIcon className="w-3.5 h-3.5" />
            <span>Donut Chart</span>
          </button>
          <button
            onClick={() => setViewMode("bar")}
            className={`p-2 rounded-lg transition flex items-center gap-1.5 text-xs font-semibold ${
              viewMode === "bar"
                ? "bg-zinc-800 text-emerald-400"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <BarIcon className="w-3.5 h-3.5" />
            <span>Bar Chart</span>
          </button>
          <button
            onClick={() => setViewMode("grid")}
            className={`p-2 rounded-lg transition flex items-center gap-1.5 text-xs font-semibold ${
              viewMode === "grid"
                ? "bg-zinc-800 text-emerald-400"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <GridIcon className="w-3.5 h-3.5" />
            <span>Grid View</span>
          </button>
        </div>
      </div>

      {/* Main Chart Viewer */}
      <div className="w-full min-h-[350px] flex items-center justify-center">
        {viewMode === "pie" && (
          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            {/* Chart Area */}
            <div className="h-[300px] w-full relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={75}
                    outerRadius={105}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={formatTooltipValue}
                    contentStyle={{
                      backgroundColor: "#09090b",
                      borderColor: "#27272a",
                      borderRadius: "12px",
                      color: "#f4f4f5"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              
              {/* Central Text inside Donut */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
                <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-500">Total Spend</span>
                <p className="text-2xl font-black text-zinc-100 mt-0.5">
                  {formatCurrency(categories.reduce((acc, curr) => acc + curr.amount, 0))}
                </p>
              </div>
            </div>

            {/* Custom Legend Area */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pr-4">
              {categories.map((cat, i) => {
                const color = CATEGORY_COLORS[cat.category] || DEFAULT_COLOR;
                return (
                  <div key={i} className="flex items-center gap-2.5 p-2.5 rounded-xl bg-zinc-900/30 border border-zinc-900/50 hover:bg-zinc-900/50 transition">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }}></span>
                    <div className="min-w-0 flex-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-zinc-200 truncate">{cat.category}</span>
                        <span className="text-zinc-400 font-bold">{cat.percentage}%</span>
                      </div>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{formatCurrency(cat.amount)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {viewMode === "bar" && (
          <div className="h-[320px] w-full pr-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 10, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1f1f23" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="#52525b" 
                  fontSize={10} 
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  stroke="#52525b" 
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => `₹${val >= 1000 ? (val / 1000).toFixed(0) + 'k' : val}`}
                />
                <Tooltip 
                  formatter={formatTooltipValue}
                  contentStyle={{
                    backgroundColor: "#09090b",
                    borderColor: "#27272a",
                    borderRadius: "12px",
                    color: "#f4f4f5"
                  }}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={45}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {viewMode === "grid" && (
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {categories.map((cat, i) => {
              const color = CATEGORY_COLORS[cat.category] || DEFAULT_COLOR;
              return (
                <div key={i} className="border border-zinc-800 rounded-xl p-4 bg-zinc-900/20 flex flex-col justify-between hover:border-zinc-700 transition">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }}></span>
                    <span className="text-sm font-bold text-zinc-200">{cat.category}</span>
                  </div>
                  <div className="flex justify-between items-baseline mt-2">
                    <span className="text-lg font-black text-zinc-100">{formatCurrency(cat.amount)}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-semibold">{cat.percentage}%</span>
                  </div>
                  <div className="w-full bg-zinc-950 rounded-full h-1 mt-3 overflow-hidden">
                    <div 
                      className="h-full rounded-full" 
                      style={{ 
                        backgroundColor: color, 
                        width: `${cat.percentage}%` 
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
