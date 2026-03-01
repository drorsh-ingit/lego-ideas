"use client";
import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { StepIndicator } from "@/components/StepIndicator";
import { MatchResultCard } from "@/components/MatchResultCard";
import { MissingPiecesList } from "@/components/MissingPiecesList";
import { useResults, useColors } from "@/lib/queries";
import { getResultDetail, runMatch } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import type { MatchResult, MatchMode } from "@/types/api";

export default function ResultsPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  const router = useRouter();
  const qc = useQueryClient();
  const { matchMode, setMatchMode, clearSession } = useSessionStore();
  const { data: results = [], isLoading } = useResults(sessionId, matchMode);
  const { data: colors = [] } = useColors();
  const [expandedSet, setExpandedSet] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<Record<string, MatchResult>>({});
  const [loadingDetail, setLoadingDetail] = useState<string | null>(null);
  const [rematching, setRematching] = useState(false);
  const [rematchError, setRematchError] = useState<string | null>(null);

  const handleViewDetails = async (setNum: string) => {
    if (expandedSet === setNum) {
      setExpandedSet(null);
      return;
    }
    setExpandedSet(setNum);
    if (!detailData[setNum]) {
      setLoadingDetail(setNum);
      try {
        const detail = await getResultDetail(sessionId, setNum, matchMode);
        setDetailData((prev) => ({ ...prev, [setNum]: detail }));
      } catch {
        // If detail fetch fails, we still show the card without missing parts
      } finally {
        setLoadingDetail(null);
      }
    }
  };

  const handleModeChange = async (mode: MatchMode) => {
    if (mode === matchMode || rematching) return;
    setMatchMode(mode);
    setRematching(true);
    setRematchError(null);
    setExpandedSet(null);
    try {
      await runMatch(sessionId, mode);
      qc.invalidateQueries({ queryKey: ["results", sessionId, mode] });
    } catch (err) {
      setRematchError(
        err instanceof Error ? err.message : "Rematching failed. Please try again."
      );
    } finally {
      setRematching(false);
    }
  };

  const handleStartOver = () => {
    clearSession();
    router.push("/");
  };

  return (
    <div className="space-y-6">
      <StepIndicator currentStep={3} />

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Matching Sets</h1>
          <p className="text-gray-500 mt-1">
            {isLoading
              ? "Loading results..."
              : results.length > 0
              ? `Showing top ${results.length} set${results.length !== 1 ? "s" : ""} sorted by match percentage`
              : "No results yet"}
          </p>
        </div>
        <button
          onClick={handleStartOver}
          className="text-sm text-gray-400 hover:text-gray-700 underline underline-offset-2 whitespace-nowrap transition-colors"
        >
          Start Over
        </button>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-3">
        {(["color_sensitive", "color_agnostic"] as MatchMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => handleModeChange(mode)}
            disabled={rematching}
            className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors
              ${
                matchMode === mode
                  ? "bg-red-600 text-white border-red-600"
                  : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
              }
              disabled:opacity-60`}
          >
            {mode === "color_sensitive" ? "Color Sensitive" : "Color Agnostic"}
          </button>
        ))}
      </div>

      {rematchError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {rematchError}
        </div>
      )}

      {/* Results list */}
      {rematching ? (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-2 border-gray-200 border-t-red-500 rounded-full animate-spin mb-3" />
          <p className="text-gray-400">Re-running match...</p>
        </div>
      ) : isLoading ? (
        <div className="text-center py-16">
          <div className="inline-block w-8 h-8 border-2 border-gray-200 border-t-red-500 rounded-full animate-spin mb-3" />
          <p className="text-gray-400">Loading results...</p>
        </div>
      ) : results.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-400 text-lg mb-2">No matching sets found.</p>
          <p className="text-gray-300 text-sm">
            Try switching to Color Agnostic mode or go back to add more pieces.
          </p>
          <button
            onClick={() => router.push(`/sessions/${sessionId}/review`)}
            className="mt-4 text-sm text-red-600 hover:text-red-700 underline underline-offset-2 transition-colors"
          >
            Back to Review
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((result) => {
            const isExpanded = expandedSet === result.set_num;
            const detail = detailData[result.set_num];
            const isLoadingThisDetail = loadingDetail === result.set_num;

            return (
              <div key={result.set_num}>
                <MatchResultCard
                  result={result}
                  onViewDetails={handleViewDetails}
                  isExpanded={isExpanded}
                />
                {isExpanded && (
                  <div className="bg-white border border-t-0 border-gray-200 rounded-b-xl px-4 pb-4 pt-3">
                    <h3 className="font-semibold text-gray-700 mb-3 text-sm">
                      Missing Pieces
                    </h3>
                    {isLoadingThisDetail ? (
                      <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
                        <span className="inline-block w-4 h-4 border-2 border-gray-200 border-t-gray-500 rounded-full animate-spin" />
                        Loading missing pieces...
                      </div>
                    ) : detail?.missing_parts ? (
                      <MissingPiecesList
                        missing={detail.missing_parts}
                        colors={colors}
                      />
                    ) : (
                      <p className="text-sm text-gray-400">
                        No detail data available.
                      </p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
