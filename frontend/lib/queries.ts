import { useQuery } from "@tanstack/react-query";
import * as api from "./api";
import type { MatchMode } from "@/types/api";

export const useSession = (sessionId: string | null) =>
  useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => api.getSession(sessionId!),
    enabled: !!sessionId,
  });

export const usePhoto = (sessionId: string, photoId: string, enabled = true) =>
  useQuery({
    queryKey: ["photo", sessionId, photoId],
    queryFn: () => api.getPhoto(sessionId, photoId),
    enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 1500 : false;
    },
  });

export const useBom = (sessionId: string | null) =>
  useQuery({
    queryKey: ["bom", sessionId],
    queryFn: () => api.getBom(sessionId!),
    enabled: !!sessionId,
  });

export const useResults = (
  sessionId: string | null,
  mode: MatchMode,
  enabled = true
) =>
  useQuery({
    queryKey: ["results", sessionId, mode],
    queryFn: () => api.getResults(sessionId!, mode),
    enabled: !!sessionId && enabled,
  });

export const useColors = () =>
  useQuery({
    queryKey: ["colors"],
    queryFn: api.getColors,
    staleTime: Infinity,
  });
