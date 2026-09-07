"use client";

import { useState } from "react";
import {
  hasClarifyingOptions,
  type ClarifyingPrompt,
  type MatchItem,
  type QueryResponse,
} from "@/lib/query";

export const LOCATION_EMPTY_COPY = "χωρίς ράφι / δεν υπάρχει τοποθεσία";
export const CATALOG_EMPTY_COPY =
  "Δεν βρέθηκαν σχετικά είδη στον κατάλογο. Δεν εφευρίσκονται προδιαγραφές ή θέσεις.";

export function Avatar() {
  return (
    <div
      style={{
        width: "28px",
        height: "28px",
        borderRadius: "999px",
        backgroundColor: "#e5e7eb",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "14px",
        color: "#4b5563",
        flexShrink: 0,
      }}
    >
      A
    </div>
  );
}

export function SummaryBubble({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        padding: "10px 14px",
        borderRadius: "18px",
        backgroundColor: "#ffffff",
        color: "#111827",
        fontSize: "14px",
        whiteSpace: "pre-wrap",
        border: "1px solid #e5e7eb",
        boxShadow: "0 4px 10px rgba(15,23,42,0.08)",
        borderBottomLeftRadius: "4px",
      }}
    >
      {children}
    </div>
  );
}

export function EmptyCatalogState({ message }: { message: string }) {
  return (
    <div
      style={{
        padding: "16px 16px 14px",
        borderRadius: "12px",
        backgroundColor: "#fffbeb",
        border: "1px solid #fde68a",
        color: "#78350f",
      }}
    >
      <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "6px" }}>
        Κενό αποτέλεσμα καταλόγου
      </div>
      <div style={{ fontSize: "14px", lineHeight: 1.45 }}>{message}</div>
    </div>
  );
}

export function MatchCard({
  match,
  fullWidth = false,
}: {
  match: MatchItem;
  fullWidth?: boolean;
}) {
  const shelfPresent =
    match.location_state === "present" && Boolean(match.location);

  return (
    <article
      style={{
        width: "100%",
        boxSizing: "border-box",
        padding: fullWidth ? "16px 18px" : "12px 14px",
        borderRadius: "12px",
        backgroundColor: "#ffffff",
        border: fullWidth ? "1px solid #93c5fd" : "1px solid #e5e7eb",
        boxShadow: fullWidth
          ? "0 8px 20px rgba(37,99,235,0.10)"
          : "0 2px 8px rgba(15,23,42,0.06)",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "8px",
          marginBottom: "6px",
        }}
      >
        <span
          style={{
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            fontSize: "13px",
            fontWeight: 700,
            color: "#1e3a8a",
            backgroundColor: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: "6px",
            padding: "2px 8px",
          }}
        >
          {match.code || "—"}
        </span>
        <span style={{ fontSize: "14px", fontWeight: 600, color: "#111827" }}>
          {match.description || "Χωρίς περιγραφή"}
        </span>
      </div>

      {match.explain && (
        <p
          style={{
            margin: "0 0 10px",
            fontSize: "13px",
            lineHeight: 1.5,
            color: "#374151",
            whiteSpace: "pre-wrap",
          }}
        >
          {match.explain}
        </p>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          fontSize: "12px",
        }}
      >
        <span style={{ fontWeight: 700, color: "#6b7280" }}>Ράφι</span>
        {shelfPresent ? (
          <span
            style={{
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              fontWeight: 600,
              color: "#065f46",
              backgroundColor: "#ecfdf5",
              border: "1px solid #a7f3d0",
              borderRadius: "6px",
              padding: "2px 8px",
            }}
          >
            {match.location}
          </span>
        ) : (
          <span
            style={{
              color: "#92400e",
              backgroundColor: "#fffbeb",
              border: "1px solid #fde68a",
              borderRadius: "6px",
              padding: "2px 8px",
            }}
          >
            {LOCATION_EMPTY_COPY}
          </span>
        )}
      </div>
    </article>
  );
}

export function SingleResult({ match }: { match: MatchItem }) {
  return (
    <div style={{ width: "100%" }}>
      <div
        style={{
          fontSize: "12px",
          fontWeight: 700,
          color: "#1d4ed8",
          letterSpacing: "0.01em",
          paddingLeft: "2px",
          marginBottom: "8px",
        }}
      >
        Βρέθηκε ο κωδικός
      </div>
      <MatchCard match={match} fullWidth />
    </div>
  );
}

export function ListResults({ matches }: { matches: MatchItem[] }) {
  return (
    <>
      <div
        style={{
          fontSize: "12px",
          fontWeight: 600,
          color: "#4b5563",
          paddingLeft: "2px",
        }}
      >
        {matches.length} {matches.length === 1 ? "αποτέλεσμα" : "αποτελέσματα"}
      </div>
      {matches.map((match, index) => (
        <MatchCard key={`${match.code || "match"}-${index}`} match={match} />
      ))}
    </>
  );
}

export function ClarifyingPromptView({
  result,
  disabled,
  onSelect,
}: {
  result: QueryResponse;
  disabled: boolean;
  onSelect: (value: string) => void;
}) {
  const [freeText, setFreeText] = useState("");
  const clarifying = result.clarifying as ClarifyingPrompt;
  const question =
    result.nl_response?.trim() ||
    clarifying.label ||
    "Χρειάζεται μια διευκρίνιση από τον κατάλογο.";
  const options = hasClarifyingOptions(result) ? clarifying.options : [];

  function submitFreeText() {
    const value = freeText.trim();
    if (!value || disabled) return;
    onSelect(value);
    setFreeText("");
  }

  return (
    <>
      <SummaryBubble>{question}</SummaryBubble>
      {options.length > 0 && (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "8px",
          }}
        >
          {clarifying.label ? (
            <span
              style={{
                width: "100%",
                fontSize: "12px",
                fontWeight: 700,
                color: "#4b5563",
              }}
            >
              {clarifying.label}
            </span>
          ) : null}
          {options.map((option) => (
            <button
              key={option}
              type="button"
              disabled={disabled}
              onClick={() => onSelect(option)}
              style={{
                padding: "7px 12px",
                borderRadius: "999px",
                border: "1px solid #bfdbfe",
                backgroundColor: disabled ? "#f3f4f6" : "#eff6ff",
                color: "#1e3a8a",
                fontSize: "13px",
                fontWeight: 600,
                cursor: disabled ? "not-allowed" : "pointer",
              }}
            >
              {option}
            </button>
          ))}
        </div>
      )}
      <div
        style={{
          display: "flex",
          gap: "8px",
          alignItems: "center",
        }}
      >
        <input
          value={freeText}
          disabled={disabled}
          onChange={(e) => setFreeText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              submitFreeText();
            }
          }}
          placeholder="Ή γράψτε…"
          aria-label="Ή γράψτε…"
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: "999px",
            border: "1px solid #d1d5db",
            fontSize: "13px",
            outline: "none",
            backgroundColor: "#ffffff",
          }}
        />
        <button
          type="button"
          disabled={disabled || !freeText.trim()}
          onClick={submitFreeText}
          style={{
            padding: "8px 12px",
            borderRadius: "999px",
            border: "none",
            fontSize: "13px",
            fontWeight: 600,
            color: "#ffffff",
            backgroundColor:
              disabled || !freeText.trim() ? "#d1d5db" : "#0b93f6",
            cursor: disabled || !freeText.trim() ? "not-allowed" : "pointer",
          }}
        >
          OK
        </button>
      </div>
    </>
  );
}
