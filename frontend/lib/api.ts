import type { Session, Photo, BomEntry, MatchResult, Color, Part, MatchMode } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// Sessions
export const createSession = () =>
  apiFetch<Session>("/sessions", { method: "POST", body: "{}" });

export const getSession = (id: string) =>
  apiFetch<Session>(`/sessions/${id}`);

// Photos
export const uploadPhotos = (sessionId: string, files: File[]) => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return fetch(`${API_BASE}/sessions/${sessionId}/photos`, {
    method: "POST",
    body: form,
  }).then(async (r) => {
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<Photo[]>;
  });
};

export const getPhoto = (sessionId: string, photoId: string) =>
  apiFetch<Photo>(`/sessions/${sessionId}/photos/${photoId}`);

export const confirmPhotos = (sessionId: string) =>
  apiFetch<{ status: string }>(`/sessions/${sessionId}/photos/confirm`, {
    method: "POST",
    body: "{}",
  });

// BOM
export const getBom = (sessionId: string) =>
  apiFetch<BomEntry[]>(`/sessions/${sessionId}/bom`);

export const addBomEntry = (
  sessionId: string,
  data: { part_num: string; color_id?: number | null; quantity: number }
) =>
  apiFetch<BomEntry>(`/sessions/${sessionId}/bom`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateBomEntry = (
  sessionId: string,
  entryId: string,
  data: { quantity?: number; color_id?: number | null }
) =>
  apiFetch<BomEntry>(`/sessions/${sessionId}/bom/${entryId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deleteBomEntry = (sessionId: string, entryId: string) =>
  fetch(`${API_BASE}/sessions/${sessionId}/bom/${entryId}`, {
    method: "DELETE",
  });

// Matching
export const runMatch = (sessionId: string, mode: MatchMode) =>
  apiFetch<{ status: string; results_count: number }>(
    `/sessions/${sessionId}/match`,
    { method: "POST", body: JSON.stringify({ mode }) }
  );

export const getResults = (sessionId: string, mode: MatchMode, page = 1) =>
  apiFetch<MatchResult[]>(
    `/sessions/${sessionId}/results?mode=${mode}&page=${page}&page_size=20`
  );

export const getResultDetail = (
  sessionId: string,
  setNum: string,
  mode: MatchMode
) =>
  apiFetch<MatchResult>(
    `/sessions/${sessionId}/results/${setNum}?mode=${mode}`
  );

// Reference
export const searchParts = (search: string) =>
  apiFetch<Part[]>(`/parts?search=${encodeURIComponent(search)}`);

export const getColors = () => apiFetch<Color[]>("/colors");
