/** Locked POST /query contract from the demo-slice backend. */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type LocationState = "present" | "empty";

export type MatchItem = {
  code: string;
  description: string;
  location: string | null;
  location_state: LocationState;
  explain: string;
  score?: number;
};

export type QueryRequest = {
  query: string;
  top_k?: number;
};

export type QueryResponse = {
  matches: MatchItem[];
  empty: boolean;
  nl_response?: string;
};

export function isCatalogEmpty(response: QueryResponse): boolean {
  return response.empty || response.matches.length === 0;
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function parseMatch(raw: unknown): MatchItem | null {
  if (!raw || typeof raw !== "object") return null;
  const item = raw as Record<string, unknown>;
  const location =
    item.location == null || item.location === ""
      ? null
      : String(item.location);
  const location_state: LocationState =
    item.location_state === "present" && location ? "present" : "empty";
  const score =
    typeof item.score === "number" && Number.isFinite(item.score)
      ? item.score
      : undefined;

  return {
    code: asString(item.code),
    description: asString(item.description),
    location,
    location_state,
    explain: asString(item.explain),
    ...(score !== undefined ? { score } : {}),
  };
}

export function parseQueryResponse(data: unknown): QueryResponse {
  if (!data || typeof data !== "object") {
    throw new Error("Μη έγκυρη απάντηση από τον διακομιστή");
  }

  const raw = data as Record<string, unknown>;
  const matches = Array.isArray(raw.matches)
    ? raw.matches
        .map(parseMatch)
        .filter((match): match is MatchItem => match !== null)
    : [];

  const nl =
    typeof raw.nl_response === "string"
      ? raw.nl_response
      : typeof raw.natural_language_response === "string"
        ? raw.natural_language_response
        : undefined;

  return {
    matches,
    empty: Boolean(raw.empty) || matches.length === 0,
    ...(nl ? { nl_response: nl } : {}),
  };
}
