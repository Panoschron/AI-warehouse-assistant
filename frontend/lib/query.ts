/** Locked POST /query contract (presentation + clarifying slice). */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type LocationState = "present" | "empty";

export type Presentation = "single" | "list" | "clarifying" | "empty";

export type MatchItem = {
  code: string;
  description: string;
  location: string | null;
  location_state: LocationState;
  explain: string;
  score?: number;
};

export type QueryConstraint = {
  field: string;
  value: string;
};

export type QueryRequest = {
  query: string;
  top_k?: number;
  constraints?: QueryConstraint[];
};

export type ClarifyingPrompt = {
  field: string;
  label: string;
  options: string[];
};

export type QueryResponse = {
  /** Eng contract: always set. Defensive fallback to "list" if the field is missing. */
  presentation: Presentation;
  matches: MatchItem[];
  clarifying: ClarifyingPrompt | null;
  empty: boolean;
  nl_response?: string;
};

const PRESENTATIONS = new Set<Presentation>([
  "single",
  "list",
  "clarifying",
  "empty",
]);

export function isCatalogEmpty(response: QueryResponse): boolean {
  return resolvePresentationView(response) === "empty";
}

/**
 * UI mode after applying Eng presentation:
 * - missing `presentation` → list (defensive only)
 * - clarifying without catalog options/field → empty or list from `empty` / matches
 * - never invent chip options; never render matches behind clarifying chips
 * - single with no match → empty
 */
export function resolvePresentationView(
  response: QueryResponse,
): Presentation {
  if (response.presentation === "empty" || response.empty) {
    return "empty";
  }

  if (response.presentation === "clarifying") {
    if (hasClarifyingOptions(response)) {
      return "clarifying";
    }
    return response.matches.length > 0 ? "list" : "empty";
  }

  if (response.presentation === "single") {
    return response.matches[0] ? "single" : "empty";
  }

  return response.matches.length > 0 ? "list" : "empty";
}

export function hasClarifyingOptions(response: QueryResponse): boolean {
  if (response.presentation !== "clarifying" || !response.clarifying) {
    return false;
  }
  const field = response.clarifying.field.trim();
  return field.length > 0 && response.clarifying.options.length > 0;
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

function parseClarifying(raw: unknown): ClarifyingPrompt | null {
  if (!raw || typeof raw !== "object") return null;
  const item = raw as Record<string, unknown>;
  const options = Array.isArray(item.options)
    ? item.options
        .filter((option): option is string => typeof option === "string")
        .map((option) => option.trim())
        .filter(Boolean)
    : [];

  return {
    field: asString(item.field).trim(),
    label: asString(item.label).trim(),
    options,
  };
}

function parsePresentation(raw: unknown): Presentation {
  return typeof raw === "string" && PRESENTATIONS.has(raw as Presentation)
    ? (raw as Presentation)
    : "list";
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

  const presentation = parsePresentation(raw.presentation);
  const clarifying =
    presentation === "clarifying" ? parseClarifying(raw.clarifying) : null;

  const nl =
    typeof raw.nl_response === "string"
      ? raw.nl_response
      : typeof raw.natural_language_response === "string"
        ? raw.natural_language_response
        : undefined;

  return {
    presentation,
    matches,
    clarifying,
    empty: presentation === "empty" || Boolean(raw.empty),
    ...(nl ? { nl_response: nl } : {}),
  };
}

export async function postQuery(
  request: QueryRequest,
): Promise<QueryResponse> {
  const body: QueryRequest = { query: request.query };
  if (request.top_k != null) body.top_k = request.top_k;
  if (request.constraints?.length) body.constraints = request.constraints;

  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* ignore non-JSON */
  }

  if (!res.ok) {
    const detail =
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : null;
    throw new Error(detail ?? `HTTP ${res.status}`);
  }

  return parseQueryResponse(data);
}
