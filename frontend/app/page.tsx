"use client";

import { useState } from "react";
import {
  CATALOG_EMPTY_COPY,
  Avatar,
  ClarifyingPromptView,
  EmptyCatalogState,
  ListResults,
  SingleResult,
  SummaryBubble,
} from "./query-result";
import {
  postQuery,
  resolvePresentationView,
  type QueryConstraint,
  type QueryResponse,
} from "@/lib/query";

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [constraints, setConstraints] = useState<QueryConstraint[]>([]);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runQuery(
    question: string,
    constraints?: QueryConstraint[],
  ) {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await postQuery({
        query: question,
        ...(constraints?.length ? { constraints } : {}),
      });
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function doSend() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setLastQuestion(question);
    setConstraints([]);
    setInput("");
    await runQuery(question);
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    await doSend();
  }

  function handleConstraint(value: string) {
    const field = result?.clarifying?.field?.trim();
    const query = lastQuestion.trim();
    if (!field || !query || loading) return;
    const next = [
      ...constraints.filter((item) => item.field !== field),
      { field, value },
    ];
    setConstraints(next);
    void runQuery(query, next);
  }

  const hasConversation = Boolean(lastQuestion || result || error || loading);
  const view = result ? resolvePresentationView(result) : null;

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
                maxWidth: view === "single" ? "100%" : "760px",
                margin: "0 auto",
                width: "100%",
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

                    {!loading && !error && result && view === "empty" && (
                      <EmptyCatalogState
                        message={result.nl_response || CATALOG_EMPTY_COPY}
                      />
                    )}

                    {!loading && !error && result && view === "clarifying" && (
                      <ClarifyingPromptView
                        result={result}
                        disabled={loading}
                        onSelect={handleConstraint}
                      />
                    )}

                    {!loading && !error && result && view === "single" && result.matches[0] && (
                      <>
                        {result.nl_response && (
                          <SummaryBubble>{result.nl_response}</SummaryBubble>
                        )}
                        <SingleResult match={result.matches[0]} />
                      </>
                    )}

                    {!loading && !error && result && view === "list" && (
                      <>
                        {result.nl_response && (
                          <SummaryBubble>{result.nl_response}</SummaryBubble>
                        )}
                        <ListResults matches={result.matches} />
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
      title: "💬 Διευκρίνιση",
      body: "Αν το ερώτημα είναι ασαφές, εμφανίζονται επιλογές (chips) από τον κατάλογο.",
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
