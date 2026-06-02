"use client";

import { FormEvent, useMemo, useState } from "react";
import { API_URL, Application, getToken, scoreClass, setToken } from "@/lib/api";

export default function ScreenPage() {
  const [tokenInput, setTokenInput] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resume, setResume] = useState("");
  const [candidateName, setCandidateName] = useState("");
  const [streamText, setStreamText] = useState("");
  const [result, setResult] = useState<Application | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => jobDescription.trim() && resume.trim() && !loading, [jobDescription, resume, loading]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setStreamText("");
    setLoading(true);

    if (tokenInput.trim()) {
      setToken(tokenInput.trim());
    }

    try {
      const response = await fetch(`${API_URL}/screen/stream/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${tokenInput.trim() || getToken()}`
        },
        body: JSON.stringify({
          job_description: jobDescription,
          resume,
          candidate_name: candidateName
        })
      });

      if (!response.ok || !response.body) {
        throw new Error(await response.text());
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const messages = buffer.split("\n\n");
        buffer = messages.pop() || "";

        for (const message of messages) {
          const line = message.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;
          const payload = JSON.parse(line.replace("data: ", ""));
          if (payload.type === "chunk") {
            setStreamText((current) => current + payload.content);
          }
          if (payload.type === "complete") {
            setResult(payload.application);
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Screening failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1 className="page-title">Screen candidate</h1>
      <div className="workspace">
        <form className="panel" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="token">JWT access token</label>
            <input
              id="token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              placeholder="Paste token from /api/token/"
            />
          </div>
          <div className="field">
            <label htmlFor="candidate">Candidate name</label>
            <input
              id="candidate"
              value={candidateName}
              onChange={(event) => setCandidateName(event.target.value)}
              placeholder="Optional; otherwise derived from resume"
            />
          </div>
          <div className="field">
            <label htmlFor="job">Job description</label>
            <textarea id="job" value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="resume">Candidate resume</label>
            <textarea id="resume" value={resume} onChange={(event) => setResume(event.target.value)} />
          </div>
          <div className="actions">
            <button disabled={!canSubmit}>{loading ? "Screening..." : "Submit screening"}</button>
            {error ? <span className="muted">{error}</span> : null}
          </div>
        </form>

        <section className="panel">
          <h2>AI result</h2>
          {result ? (
            <>
              <span className={`score ${scoreClass(result.ai_score)}`}>{result.ai_score}</span>
              <ul className="reasons">
                {result.ai_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </>
          ) : (
            <p className="muted">The streamed response will appear here as the model generates it.</p>
          )}
          <div className="stream">{streamText}</div>
        </section>
      </div>
    </main>
  );
}
