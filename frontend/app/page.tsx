"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSession } from "@/lib/api";
import { useSessionStore } from "@/lib/store";

export default function HomePage() {
  const router = useRouter();
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      const session = await createSession();
      setSessionId(session.id);
      router.push(`/sessions/${session.id}/upload`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center text-center py-16 gap-6">
      <h1 className="text-4xl font-bold text-gray-900">
        Find Lego Sets From Your Pieces
      </h1>
      <p className="text-lg text-gray-500 max-w-lg">
        Photograph your loose Lego bricks, and we&apos;ll identify them and show
        which sets you can build — partially or completely.
      </p>
      <div className="flex flex-col gap-3 text-left text-gray-600 text-sm max-w-md w-full bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex gap-3 items-start">
          <span className="text-xl">📷</span>
          <div>
            <strong>1. Upload</strong> — Take 1-5 photos of your pieces spread flat
          </div>
        </div>
        <div className="flex gap-3 items-start">
          <span className="text-xl">✏️</span>
          <div>
            <strong>2. Review</strong> — Correct any identification errors, assign colors
          </div>
        </div>
        <div className="flex gap-3 items-start">
          <span className="text-xl">🏆</span>
          <div>
            <strong>3. Match</strong> — See which sets you can build and what&apos;s missing
          </div>
        </div>
      </div>
      <button
        onClick={handleStart}
        disabled={loading}
        className="mt-4 px-8 py-3 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-lg transition-colors disabled:opacity-60"
      >
        {loading ? "Starting..." : "Get Started"}
      </button>
    </div>
  );
}
