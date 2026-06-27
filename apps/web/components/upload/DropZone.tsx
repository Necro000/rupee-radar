"use client";

import React, { useState, useRef } from "react";
import { Upload, FileText, AlertCircle } from "lucide-react";

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  maxSizeMB?: number;
}

export default function DropZone({
  onFileSelect,
  selectedFile,
  onClear,
  maxSizeMB = 10
}: DropZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setError(null);
    
    // Check if CSV or Excel
    const isCsv = file.name.toLowerCase().endsWith(".csv");
    const isXlsx = file.name.toLowerCase().endsWith(".xlsx");
    if (!isCsv && !isXlsx) {
      setError("Unsupported file format. Please upload a CSV or Excel (.xlsx) bank statement.");
      return false;
    }

    // Check file size
    const maxSize = maxSizeMB * 1024 * 1024;
    if (file.size > maxSize) {
      setError(`File size exceeds the ${maxSizeMB} MB limit.`);
      return false;
    }

    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        onFileSelect(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        onFileSelect(file);
      }
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full flex flex-col items-center">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx"
        className="hidden"
        onChange={handleFileChange}
      />

      {!selectedFile ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
          className={`w-full max-w-2xl min-h-[220px] rounded-2xl border-2 border-dashed flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-300 backdrop-blur-md ${
            isDragActive
              ? "border-emerald-400 bg-emerald-500/10 scale-[1.01] shadow-emerald-500/10 shadow-lg"
              : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-900/60"
          }`}
        >
          <div className="h-12 w-12 rounded-xl bg-zinc-800/80 flex items-center justify-center mb-4 text-zinc-400 group-hover:text-zinc-200 transition">
            <Upload className="w-6 h-6 text-emerald-400 animate-pulse" />
          </div>
          <p className="text-zinc-200 font-semibold text-sm sm:text-base">
            Drag & drop your bank statement here
          </p>
          <p className="text-zinc-400 text-xs sm:text-sm mt-1">
            or <span className="text-emerald-400 underline font-medium">browse local files</span>
          </p>
          <p className="text-zinc-500 text-xs mt-4">
            Supports CSV or Excel (.xlsx) formats (Max {maxSizeMB} MB)
          </p>
        </div>
      ) : (
        <div className="w-full max-w-2xl bg-zinc-900/60 border border-zinc-800 rounded-2xl p-5 flex items-center justify-between backdrop-blur-md">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-zinc-200 font-medium text-sm truncate">
                {selectedFile.name}
              </p>
              <p className="text-zinc-500 text-xs">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setError(null);
              onClear();
            }}
            className="text-xs text-zinc-500 hover:text-zinc-300 px-3 py-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800 transition"
          >
            Remove
          </button>
        </div>
      )}

      {error && (
        <div className="w-full max-w-2xl mt-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-3 flex items-start gap-2.5 text-xs sm:text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
