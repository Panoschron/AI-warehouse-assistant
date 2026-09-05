"use client";

import { useState } from "react";

type LocationState = "present" | "empty";

type Match = {
  code: string;
  description: string;
  location: string | null;
  location_state: LocationState;
  explain: string;
  score?: number;
};

type QueryResponse = {
  matches?: Match[];
  empty?: boolean;
  nl_response?: string;
  natural_language_response?: string;
  answer?: string;
};

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState<string>("");
  const [matches, setMatches] = useState<Match[]>([]);
  const [empty, setEmpty] = useState(false);
  const [lastQuestion, setLastQuestion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  async function doSend(preset?: string) {
    const question = (preset ?? input).trim();
    if (!question || loading) return;

    setLoading(true);
    setError("");
    setAnswer("");
    setMatches([]);
    setEmpty(false);
    setLastQuestion(question);
    if (!preset) setInput("");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: question,
            top_k: null,
          }),
        }
      );

      let data: QueryResponse | null = null;
      try {
        data = await res.json();
      } catch {
        /* ignore */
      }

      if (!res.ok) {
        const detail = (data as { detail?: string } | null)?.detail;
        throw new Error(detail ?? `HTTP ${res.status}`);
      }

      const nextMatches = data?.matches ?? [];
      setMatches(nextMatches);
      setEmpty(Boolean(data?.empty) || nextMatches.length === 0);
      setAnswer(
        data?.nl_response ??
          data?.natural_language_response ??
          data?.answer ??
          ""
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    await doSend();
  }

  const hasThread = Boolean(lastQuestion || answer || error || loading || matches.length);

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
              Κατάλογος → ταίριασμα → εξήγηση → θέση ραφιού ή κενό
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
          {!hasThread && (
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
                Δοκίμασε ορθογραφικό λάθος ή είδος χωρίς θέση ραφιού.
              </p>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "12px",
                  textAlign: "left",
                }}
              >
                {[
                  ["🔎 Φίλτρο (typo)", "υδραυλικο φιλτρο"],
                  ["📦 Χωρίς ράφι", "ρουλεμαν 6205"],
                  ["🧠 Κενό αποτέλεσμα", "πλανητης ζευς ανταλλακτικο"],
                ].map(([title, sample]) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => {
                      setInput(sample);
                      void doSend(sample);
                    }}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "12px",
                      backgroundColor: "#ffffff",
                      border: "1px solid #e5e7eb",
                      fontSize: "12px",
                      textAlign: "left",
                      cursor: "pointer",
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
                      {title}
                    </div>
                    <div>“{sample}”</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {hasThread && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                maxWidth: "720px",
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

              {(answer || error || loading || empty || matches.length > 0) && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-start",
                    alignItems: "flex-start",
                    gap: "8px",
                  }}
                >
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
                  <div
                    style={{
                      maxWidth: "88%",
                      width: "100%",
                      padding: "10px 14px",
                      borderRadius: "18px",
                      backgroundColor: "#ffffff",
                      color: "#111827",
                      fontSize: "14px",
                      border: "1px solid #e5e7eb",
                      boxShadow: "0 4px 10px rgba(15,23,42,0.08)",
                      borderBottomLeftRadius: "4px",
                    }}
                  >
                    {loading && !answer && !error && (
                      <span style={{ color: "#6b7280" }}>
                        Ψάχνω στον κατάλογο...
                      </span>
                    )}

                    {!loading && error && (
                      <span style={{ color: "#b91c1c" }}>Error: {error}</span>
                    )}

                    {!loading && !error && (
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {answer && (
                          <div style={{ whiteSpace: "pre-wrap" }}>{answer}</div>
                        )}

                        {empty && matches.length === 0 && (
                          <div
                            style={{
                              padding: "10px 12px",
                              borderRadius: "10px",
                              backgroundColor: "#f8fafc",
                              border: "1px dashed #cbd5e1",
                              color: "#475569",
                            }}
                          >
                            Δεν βρέθηκαν σχετικά είδη στον κατάλογο.
                          </div>
                        )}

                        {matches.map((match) => (
                          <article
                            key={`${match.code}-${match.location ?? "none"}`}
                            style={{
                              padding: "10px 12px",
                              borderRadius: "10px",
                              border: "1px solid #e5e7eb",
                              backgroundColor: "#f8fafc",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                gap: "8px",
                                alignItems: "baseline",
                              }}
                            >
                              <strong style={{ color: "#111827" }}>{match.code}</strong>
                              <span
                                style={{
                                  fontSize: "12px",
                                  fontWeight: 600,
                                  color:
                                    match.location_state === "present"
                                      ? "#166534"
                                      : "#92400e",
                                  backgroundColor:
                                    match.location_state === "present"
                                      ? "#dcfce7"
                                      : "#fef3c7",
                                  borderRadius: "999px",
                                  padding: "2px 8px",
                                }}
                              >
                                {match.location_state === "present"
                                  ? `Ράφι ${match.location}`
                                  : "Χωρίς θέση στο κατάλογο"}
                              </span>
                            </div>
                            <div style={{ marginTop: "4px", color: "#374151" }}>
                              {match.description}
                            </div>
                            <div
                              style={{
                                marginTop: "8px",
                                color: "#4b5563",
                                fontSize: "13px",
                              }}
                            >
                              {match.explain}
                            </div>
                          </article>
                        ))}
                      </div>
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
            placeholder="Γράψε την ερώτησή σου εδώ..."
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
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>
    </main>
  );
}
