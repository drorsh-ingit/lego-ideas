import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { MatchMode } from "@/types/api";

interface SessionStore {
  sessionId: string | null;
  matchMode: MatchMode;
  setSessionId: (id: string) => void;
  setMatchMode: (mode: MatchMode) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      sessionId: null,
      matchMode: "color_sensitive",
      setSessionId: (id) => set({ sessionId: id }),
      setMatchMode: (mode) => set({ matchMode: mode }),
      clearSession: () => set({ sessionId: null }),
    }),
    { name: "lego-session" }
  )
);
