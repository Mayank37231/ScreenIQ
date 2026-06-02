"use client";

import { useEffect, useState } from "react";
import { apiFetch, Application, ApplicationPage, scoreClass, setToken } from "@/lib/api";

const PAGE_SIZE = 50;

export default function DashboardPage() {
  const [tokenInput, setTokenInput] = useState("");
  const [page, setPage] = useState(0);
  const [data, setData] = useState<ApplicationPage | null>(null);
  const [selected, setSelected] = useState<Application | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadPage(page);
  }, [page]);

  async function loadPage(nextPage = page) {
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<ApplicationPage>(`/applications/?limit=${PAGE_SIZE}&offset=${nextPage * PAGE_SIZE}`);
      setData(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load applications.");
    } finally {
      setLoading(false);
    }
  }

  function saveToken() {
    setToken(tokenInput.trim());
    void loadPage(0);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <main>
      <h1 className="page-title">Applications dashboard</h1>
      <section className="panel">
        <div className="actions">
          <input
            value={tokenInput}
            onChange={(event) => setTokenInput(event.target.value)}
            placeholder="Paste JWT access token"
          />
          <button type="button" onClick={saveToken}>Use token</button>
          {loading ? <span className="muted">Loading...</span> : null}
          {error ? <span className="muted">{error}</span> : null}
        </div>
      </section>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Candidate name</th>
              <th>AI score</th>
              <th>Date screened</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {(data?.results || []).map((application) => (
              <tr key={application.id}>
                <td>{application.candidate_name}</td>
                <td>
                  <span className={`score ${scoreClass(application.ai_score)}`}>{application.ai_score}</span>
                </td>
                <td>{new Date(application.created_at).toLocaleString()}</td>
                <td>
                  <button type="button" onClick={() => setSelected(application)}>View detail</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pager">
        <button type="button" disabled={page === 0} onClick={() => setPage((current) => current - 1)}>Previous</button>
        <span className="muted">Page {page + 1} of {totalPages}</span>
        <button type="button" disabled={page + 1 >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
      </div>

      {selected ? (
        <section className="panel detail">
          <h2>{selected.candidate_name}</h2>
          <p><strong>Score:</strong> {selected.ai_score}</p>
          <ul className="reasons">
            {selected.ai_reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p><strong>Job description</strong></p>
          <p>{selected.job_description}</p>
          <p><strong>Resume</strong></p>
          <p>{selected.resume}</p>
        </section>
      ) : null}
    </main>
  );
}
