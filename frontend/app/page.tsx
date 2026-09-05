"use client";

import { useState } from "react";
import {
  API_BASE,
  isCatalogEmpty,
  parseQueryResponse,
  type MatchItem,
  type QueryResponse,
} from "@/lib/query";

const LOCATION_EMPTY_COPY = "χωρίς ράφι / δεν υπάρχει τοποθεσία";
const CATALOG_EMPTY_COPY =
  "Δεν βρέθηκαν σχετικά είδη στον κατάλογο. Δεν εφευρίσκονται προδιαγραφές ή θέσεις.";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function doSend() {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setLoading(true);
    setError("");
    setResult(null);
    setLastQuestion(question);
    setInput("");

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question }),
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
          typeof data.detail === "string"
            ? data.detail
            : null;
        throw new Error(detail ?? `HTTP ${res.status}`);
      }

      setResult(parseQueryResponse(data));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    await doSend();
  }

  const hasConversation = Boolean(lastQuestion || result || error || loading);
  const emptyCatalog = result ? isCatalogEmpty(result) : false;

  return (
    <main
      style={{
        minHeight: "100vh",
        margin: 0,
        padding: "24px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background:
          "radial-gradient(circle at top, #f5f7fb 0, #e4e6f0 40%, #d0d4e0 100%)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "960px",
          height: "80vh",
          backgroundColor: "#ffffff",
          borderRadius: "16px",
          boxShadow:
            "0 18px 45px rgba(15,23,42,0.18), 0 0 0 1px rgba(148,163,184,0.18)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <header
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid #e5e7eb",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background:
              "linear-gradient(135deg, rgba(37,99,235,0.06), rgba(79,70,229,0.06))",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "999px",
              background:
                "radial-gradient(circle at 30% 30%, #93c5fd, #1d4ed8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "18px",
              color: "#fff",
              fontWeight: 600,
            }}
          >
            A
          </div>
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "18px",
                fontWeight: 600,
                color: "#111827",
              }}
            >
              AI Warehouse Assistant
            </h1>
            <p
              style={{
                margin: 0,
                marginTop: "2px",
                fontSize: "13px",
                color: "#6b7280",
              }}
            >
              Αναζήτηση καταλόγου: κωδικός, εξήγηση, ράφι — χωρίς εφεύρεση προδιαγραφών.
            </p>
          </div>
        </header>

        <div
          style={{
            flex: 1,
            padding: "16px 20px",
            backgroundColor: "#f9fafb",
            overflowY: "auto",
          }}
        >
          {!hasConversation && <LandingHints />}

          {hasConversation && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                maxWidth: "760px",
                margin: "0 auto",
              }}
            >
              {lastQuestion && (
                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  <div
                    style={{
                      maxWidth: "80%",
                      padding: "10px 14px",
                      borderRadius: "18px",
                      backgroundColor: "#0b93f6",
                      color: "#ffffff",
                      fontSize: "14px",
                      whiteSpace: "pre-wrap",
                      boxShadow: "0 4px 10px rgba(15,23,42,0.15)",
                      borderBottomRightRadius: "4px",
                    }}
                  >
                    {lastQuestion}
                  </div>
                </div>
              )}

              {(loading || error || result) && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-start",
                    alignItems: "flex-start",
                    gap: "8px",
                  }}
                >
                  <Avatar />
                  <div
                    style={{
                      flex: 1,
                      minWidth: 0,
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    {loading && !result && !error && (
                      <SummaryBubble>
                        <span style={{ color: "#6b7280" }}>
                          Αναζητώ στον κατάλογο…
                        </span>
                      </SummaryBubble>
                    )}

                    {!loading && error && (
                      <SummaryBubble>
                        <span style={{ color: "#b91c1c" }}>Error: {error}</span>
                      </SummaryBubble>
                    )}

                    {!loading && !error && result && emptyCatalog && (
                      <EmptyCatalogState
                        message={result.nl_response || CATALOG_EMPTY_COPY}
                      />
                    )}

                    {!loading && !error && result && !emptyCatalog && (
                      <>
                        {result.nl_response && (
                          <SummaryBubble>{result.nl_response}</SummaryBubble>
                        )}
                        <div
                          style={{
                            fontSize: "12px",
                            fontWeight: 600,
                            color: "#4b5563",
                            paddingLeft: "2px",
                          }}
                        >
                          {result.matches.length}{" "}
                          {result.matches.length === 1
                            ? "αποτέλεσμα"
                            : "αποτελέσματα"}
                        </div>
                        {result.matches.map((match, index) => (
                          <MatchCard
                            key={`${match.code || "match"}-${index}`}
                            match={match}
                          />
                        ))}
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <form
          onSubmit={handleSend}
          style={{
            padding: "12px 16px",
            borderTop: "1px solid #e5e7eb",
            display: "flex",
            gap: "8px",
            backgroundColor: "#ffffff",
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void doSend();
              }
            }}
            rows={2}
            placeholder="Π.χ. υδραυλικο φιλτρο, rakor, ρουλεμαν 6205…"
            style={{
              flex: 1,
              resize: "none",
              padding: "10px 12px",
              borderRadius: "999px",
              border: "1px solid #d1d5db",
              fontSize: "14px",
              outline: "none",
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              minWidth: "90px",
              padding: "10px 16px",
              borderRadius: "999px",
              border: "none",
              fontSize: "14px",
              fontWeight: 500,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              backgroundColor:
                loading || !input.trim() ? "#d1d5db" : "#0b93f6",
              color: "#ffffff",
            }}
          >
            {loading ? "…" : "Αποστολή"}
          </button>
        </form>
      </div>
    </main>
  );
}

function Avatar() {
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

function SummaryBubble({ children }: { children: React.ReactNode }) {
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

function EmptyCatalogState({ message }: { message: string }) {
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

function MatchCard({ match }: { match: MatchItem }) {
  const shelfPresent =
    match.location_state === "present" && Boolean(match.location);

  return (
    <article
      style={{
        padding: "12px 14px",
        borderRadius: "12px",
        backgroundColor: "#ffffff",
        border: "1px solid #e5e7eb",
        boxShadow: "0 2px 8px rgba(15,23,42,0.06)",
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

function LandingHints() {
  const hints = [
    {
      title: "🔎 Ορθογραφία / Greeklish",
      body: "«υδραυλικο φιλτρο» ή «rakor» — ταιριάζει και με τυπογραφικά.",
    },
    {
      title: "📦 Ράφι ή κενό",
      body: "«ρουλεμαν 6205» — αν δεν υπάρχει θέση, φαίνεται ρητά.",
    },
    {
      title: "🗂️ Κενός κατάλογος",
      body: "Άσχετο ερώτημα → σαφές empty state, χωρίς εφεύρεση ειδών.",
    },
  ];

  return (
    <div
      style={{
        maxWidth: "520px",
        margin: "40px auto 0 auto",
        textAlign: "center",
        color: "#6b7280",
        fontSize: "14px",
      }}
    >
      <h2
        style={{
          fontSize: "20px",
          marginBottom: "12px",
          color: "#111827",
        }}
      >
        Ξεκίνα μια ερώτηση
      </h2>
      <p style={{ marginBottom: "20px" }}>
        Ο βοηθός επιστρέφει κωδικό, εξήγηση από τον κατάλογο και ράφι — ποτέ
        φανταστικές προδιαγραφές.
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
          textAlign: "left",
        }}
      >
        {hints.map((hint) => (
          <div
            key={hint.title}
            style={{
              padding: "10px 12px",
              borderRadius: "12px",
              backgroundColor: "#ffffff",
              border: "1px solid #e5e7eb",
              fontSize: "12px",
            }}
          >
            <div
              style={{
                fontWeight: 600,
                fontSize: "12px",
                marginBottom: "4px",
                color: "#111827",
              }}
            >
              {hint.title}
            </div>
            <div>{hint.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
