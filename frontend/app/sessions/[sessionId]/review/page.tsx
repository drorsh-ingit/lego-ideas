"use client";
import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { StepIndicator } from "@/components/StepIndicator";
import { BomTable } from "@/components/BomTable";
import { AddPartForm } from "@/components/AddPartForm";
import { useBom, useColors } from "@/lib/queries";
import { updateBomEntry, deleteBomEntry, addBomEntry, runMatch } from "@/lib/api";
import { useSessionStore } from "@/lib/store";
import type { MatchMode } from "@/types/api";

export default function ReviewPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  const router = useRouter();
  const qc = useQueryClient();
  const { data: bom = [], isLoading } = useBom(sessionId);
  const { data: colors = [] } = useColors();
  const { matchMode, setMatchMode } = useSessionStore();
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  const invalidateBom = () =>
    qc.invalidateQueries({ queryKey: ["bom", sessionId] });

  const handleUpdate = async (
    entryId: string,
    data: { quantity?: number; color_id?: number | null }
  ) => {
    await updateBomEntry(sessionId, entryId, data);
    invalidateBom();
  };

  const handleDelete = async (entryId: string) => {
    await deleteBomEntry(sessionId, entryId);
    invalidateBom();
  };

  const handleAdd = async (data: {
    part_num: string;
    color_id?: number | null;
    quantity: number;
  }) => {
    await addBomEntry(sessionId, data);
    invalidateBom();
  };

  const handleMatch = async () => {
    setMatching(true);
    setMatchError(null);
    try {
      await runMatch(sessionId, matchMode);
      router.push(`/sessions/${sessionId}/results`);
    } catch (err) {
      setMatchError(err instanceof Error ? err.message : "Matching failed. Please try again.");
    } finally {
      setMatching(false);
    }
  };

  return (
    <div className="space-y-8">
      <StepIndicator currentStep={2} />

      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Review Identified Pieces
        </h1>
        <p className="text-gray-500 mt-1">
          Correct any errors, assign colors, and add missing pieces before
          matching.
        </p>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="inline-block w-8 h-8 border-2 border-gray-200 border-t-red-500 rounded-full animate-spin mb-3" />
          <p className="text-gray-400">Loading pieces...</p>
        </div>
      ) : (
        <BomTable
          entries={bom}
          colors={colors}
          onUpdate={handleUpdate}
          onDelete={handleDelete}
        />
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <h2 className="font-semibold text-gray-700 mb-3">Add a Piece Manually</h2>
        <AddPartForm sessionId={sessionId} colors={colors} onAdd={handleAdd} />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
        <h2 className="font-semibold text-gray-700">Matching Mode</h2>
        <div className="flex gap-3">
          {(["color_sensitive", "color_agnostic"] as MatchMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setMatchMode(mode)}
              className={`flex-1 py-2 rounded-lg border text-sm font-medium transition-colors
                ${
                  matchMode === mode
                    ? "bg-red-600 text-white border-red-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-gray-400"
                }`}
            >
              {mode === "color_sensitive" ? "Color Sensitive" : "Color Agnostic"}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400">
          {matchMode === "color_sensitive"
            ? "Colors must match exactly. Assign colors to your pieces above."
            : "Colors are ignored — parts are matched by shape only."}
        </p>

        {matchError && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
            {matchError}
          </div>
        )}

        <button
          onClick={handleMatch}
          disabled={matching || bom.length === 0}
          className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {matching ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Matching...
            </>
          ) : (
            "Find Matching Sets →"
          )}
        </button>
        {bom.length === 0 && !isLoading && (
          <p className="text-xs text-gray-400 text-center">
            Add some pieces first to run matching.
          </p>
        )}
      </div>
    </div>
  );
}
