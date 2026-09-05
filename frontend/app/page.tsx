"use client";

import { useState } from "react";

export default function ChatPage() {
  // τι γράφει ο χρήστης
  const [input, setInput] = useState("");
  // τι απάντηση πήραμε από το backend (τελευταία)
  const [answer, setAnswer] = useState<string>("");
  // τελευταία ερώτηση του χρήστη (για εμφάνιση στο chat)
  const [lastQuestion, setLastQuestion] = useState<string>("");
  // loading flag για το κουμπί
  const [loading, setLoading] = useState(false);
  // για να δείχνουμε error αν κάτι πάει στραβά
  const [error, setError] = useState<string>("");

  async function doSend() {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setLoading(true);
    setError("");
    setAnswer("");
    setLastQuestion(question);
    setInput("");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: question,
            top_k: null // ή βάλε αριθμό
          }),
        }
      );

      let data: any = null;
      try { data = await res.json(); } catch { /* ignore */ }

      if (!res.ok) {
        const detail = data?.detail;
        throw new Error(detail ?? `HTTP ${res.status}`);
      }

      setAnswer(
        data.natural_language_response ??
        data.nl_response ??
        data.answer ??
        JSON.stringify(data)
      );
    } catch (err: any) {
      setError(err?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    await doSend();
  }

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
        {/* HEADER */}
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
              Ρώτα σε φυσική γλώσσα για προϊόντα, stock, κωδικούς κτλ.
            </p>
          </div>
        </header>

        {/* CHAT AREA */}
        <div
          style={{
            flex: 1,
            padding: "16px 20px",
            backgroundColor: "#f9fafb",
            overflowY: "auto",
          }}
        >
          {/* Αν δεν υπάρχει ακόμα ερώτηση/απάντηση, δείξε placeholder σαν ChatGPT landing */}
          {!lastQuestion && !answer && !error && !loading && (
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
                Π.χ.{" "}
                <span style={{ fontStyle: "italic" }}>
                  “Βρες μου όλα τα υδραυλικά φίλτρα για Caterpillar” ή
                  “Ποιο είναι το stock στα λάστιχα 3/8;”
                </span>
              </p>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "12px",
                  textAlign: "left",
                }}
              >
                <div
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
                    🔎 Αναζήτηση προϊόντων
                  </div>
                  <div>“Δείξε μου όλους τους κωδικούς με ‘seal kit’ στο όνομα.”</div>
                </div>
                <div
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
                    📦 Stock & αποθήκη
                  </div>
                  <div>“Τι έχουμε διαθέσιμο σε εύκαμπτες σωλήνες 1/2;”</div>
                </div>
                <div
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
                    🧠 Περιγραφές
                  </div>
                  <div>“Γράψε μου περιγραφή για αυτό το προϊόν για e-shop.”</div>
                </div>
              </div>
            </div>
          )}

          {/* Αν υπάρχει τελευταία ερώτηση ή απάντηση, εμφάνισέ τες σαν chat */}
          {(lastQuestion || answer || error || loading) && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "12px",
                maxWidth: "720px",
                margin: "0 auto",
              }}
            >
              {/* Μήνυμα χρήστη */}
              {lastQuestion && (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                  }}
                >
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

              {/* Μήνυμα assistant (loading / error / answer) */}
              {(answer || error || loading) && (
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
                      maxWidth: "80%",
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
                    {loading && !answer && !error && (
                      <span style={{ color: "#6b7280" }}>
                        Γράφω απάντηση...
                      </span>
                    )}

                    {!loading && error && (
                      <span style={{ color: "#b91c1c" }}>
                        Error: {error}
                      </span>
                    )}

                    {!loading && !error && answer && <>{answer}</>}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* INPUT BAR */}
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
