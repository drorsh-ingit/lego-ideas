"use client";
import Image from "next/image";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { MatchResult } from "@/types/api";

interface MatchResultCardProps {
  result: MatchResult;
  onViewDetails: (setNum: string) => void;
  isExpanded?: boolean;
}

function getMatchColor(pct: number): string {
  if (pct >= 80) return "text-green-600";
  if (pct >= 50) return "text-yellow-600";
  return "text-red-600";
}

function getProgressColor(pct: number): string {
  if (pct >= 80) return "bg-green-500";
  if (pct >= 50) return "bg-yellow-500";
  return "bg-red-500";
}

export function MatchResultCard({
  result,
  onViewDetails,
  isExpanded = false,
}: MatchResultCardProps) {
  const matchPct = Math.round(result.match_percentage);
  const matchColorClass = getMatchColor(matchPct);
  const progressColorClass = getProgressColor(matchPct);

  return (
    <div
      className={`bg-white border border-gray-200 shadow-sm overflow-hidden transition-all ${
        isExpanded ? "rounded-t-xl" : "rounded-xl"
      }`}
    >
      <div className="flex gap-4 p-4">
        {/* Set image */}
        <div className="flex-shrink-0 w-24 h-24 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center">
          {result.set_img_url ? (
            <Image
              src={result.set_img_url}
              alt={result.set_name}
              width={96}
              height={96}
              className="object-contain w-full h-full"
              unoptimized
            />
          ) : (
            <span className="text-4xl select-none" aria-hidden>
              🧱
            </span>
          )}
        </div>

        {/* Set info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="font-semibold text-gray-900 truncate text-base leading-tight">
                {result.set_name}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="font-mono text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                  {result.set_num}
                </span>
                {result.set_year && (
                  <span className="text-xs text-gray-400">{result.set_year}</span>
                )}
              </div>
            </div>

            {/* Match percentage */}
            <div className={`text-right flex-shrink-0 ${matchColorClass}`}>
              <div className="text-3xl font-bold leading-none">{matchPct}%</div>
              <div className="text-xs font-medium mt-0.5 text-gray-400">match</div>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-3">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${progressColorClass}`}
                style={{ width: `${Math.min(matchPct, 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {result.parts_matched} / {result.parts_total} parts matched
            </p>
          </div>
        </div>
      </div>

      {/* View details button */}
      <div className="px-4 pb-3">
        <button
          onClick={() => onViewDetails(result.set_num)}
          className="flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-red-600 transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp size={16} />
              Hide Missing Pieces
            </>
          ) : (
            <>
              <ChevronDown size={16} />
              Show Missing Pieces
            </>
          )}
        </button>
      </div>
    </div>
  );
}
