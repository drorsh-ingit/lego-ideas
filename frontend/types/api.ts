export type SessionStatus = "pending" | "identifying" | "identified" | "matching" | "complete";
export type PhotoStatus = "pending" | "processing" | "done" | "failed";
export type MatchMode = "color_sensitive" | "color_agnostic";

export interface Session {
  id: string;
  status: SessionStatus;
  created_at: string;
  expires_at: string;
}

export interface Photo {
  id: string;
  session_id: string;
  filename: string;
  status: PhotoStatus;
  raw_response: Record<string, unknown> | null;
  created_at: string;
}

export interface BomEntry {
  id: string;
  session_id: string;
  part_num: string;
  color_id: number | null;
  quantity: number;
  confidence: number | null;
  source: string;
  created_at: string;
}

export interface MissingPart {
  part_num: string;
  color_id: number | null;
  needed: number;
  have: number;
}

export interface MatchResult {
  session_id: string;
  set_num: string;
  set_name: string;
  set_year: number | null;
  set_img_url: string | null;
  match_mode: MatchMode;
  match_percentage: number;
  parts_matched: number;
  parts_total: number;
  missing_parts?: MissingPart[];
}

export interface Color {
  id: number;
  name: string;
  rgb: string;
  is_trans: boolean;
}

export interface Part {
  part_num: string;
  name: string;
}
