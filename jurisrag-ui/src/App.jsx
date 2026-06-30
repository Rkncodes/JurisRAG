import { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from "docx";
import { saveAs } from "file-saver";
import "./App.css";

const API = "http://127.0.0.1:8000";
const HISTORY_KEY   = "legal-rag-history";
const BOOKMARK_KEY  = "legal-rag-bookmarks";

function parseAnswer(raw) {
  if (!raw) return { text: "", sources: [] };
  const parts = raw.split("SOURCES USED");
  const text = parts[0].trim();
  const sources = [];
  if (parts[1]) {
    const lines = parts[1].split("\n");
    let current = {};
    for (const line of lines) {
      const l = line.trim();
      if (l.startsWith("PDF Name")) current.pdf = l.split(":").slice(1).join(":").trim();
      if (l.startsWith("Page No")) {
        current.page = l.split(":").slice(1).join(":").trim();
        if (current.pdf) { sources.push({ ...current }); current = {}; }
      }
    }
  }
  return { text, sources };
}

function App() {
  const [question, setQuestion]           = useState("");
  const [answer, setAnswer]               = useState("");
  const [keyword, setKeyword]             = useState("");
  const [matches, setMatches]             = useState([]);
  const [globalKeyword, setGlobalKeyword] = useState("");
  const [globalResults, setGlobalResults] = useState([]);
  const [agreement, setAgreement]         = useState("");
  const [agreements, setAgreements]       = useState([]);
  const [loading, setLoading]             = useState(false);
  const [confidence, setConfidence]       = useState(0);
  const [parsedSources, setParsedSources] = useState([]);
  const [copied, setCopied]               = useState(false);
  const [tables, setTables]               = useState([]);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [expandedTable, setExpandedTable] = useState(null);

  const [awaitingSelection, setAwaitingSelection] = useState(false);
  const [agreementOptions, setAgreementOptions]   = useState([]);
  const [pendingQuestion, setPendingQuestion]     = useState("");
  const [pinnedAgreement, setPinnedAgreement]     = useState(null);

  const [viewerPdf, setViewerPdf]   = useState(null);
  const [viewerPage, setViewerPage] = useState(1);
  const [citedPages, setCitedPages] = useState([]);
  const [citedIndex, setCitedIndex] = useState(0);
  const iframeRef                   = useRef(null);
  const answerRef                   = useRef(null);

  const [history, setHistory] = useState(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
    catch { return []; }
  });

  const [bookmarks, setBookmarks] = useState(() => {
    try { return JSON.parse(localStorage.getItem(BOOKMARK_KEY)) || []; }
    catch { return []; }
  });

  const [activeTab, setActiveTab]         = useState("ask");
  const [historySearch, setHistorySearch] = useState("");
  const [darkMode, setDarkMode]           = useState(true);

  const saveToHistory = (q, a, pdf) => {
    const entry = { id: Date.now(), question: q, answer: a, pdf: pdf || null, timestamp: new Date().toLocaleString() };
    const updated = [entry, ...history].slice(0, 100);
    setHistory(updated);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  };

  const toggleBookmark = () => {
    if (!answerText || !question) return;
    const existing = bookmarks.find(b => b.question === question);
    if (existing) {
      const updated = bookmarks.filter(b => b.question !== question);
      setBookmarks(updated);
      localStorage.setItem(BOOKMARK_KEY, JSON.stringify(updated));
    } else {
      const entry = {
        id: Date.now(),
        question,
        answer,
        pdf: viewerPdf || null,
        sources: parsedSources,
        timestamp: new Date().toLocaleString(),
      };
      const updated = [entry, ...bookmarks].slice(0, 50);
      setBookmarks(updated);
      localStorage.setItem(BOOKMARK_KEY, JSON.stringify(updated));
    }
  };

  const isBookmarked = bookmarks.some(b => b.question === question);

  const restoreFromHistory = (entry) => {
    setQuestion(entry.question);
    setAnswer(entry.answer);
    const { sources } = parseAnswer(entry.answer);
    setParsedSources(sources);
    setActiveTab("ask");
    if (entry.pdf) {
      setViewerPdf(entry.pdf);
      setViewerPage(1);
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = "";
          setTimeout(() => { iframeRef.current.src = getPdfUrl(entry.pdf, 1); }, 50);
        }
      }, 100);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  };

  const getPdfUrl = (pdfName, page) =>
    `${API}/pdf/${encodeURIComponent(pdfName)}#page=${page}`;

  const jumpToPage = (page) => {
    setViewerPage(page);
    if (iframeRef.current && viewerPdf) {
      iframeRef.current.src = "";
      setTimeout(() => { iframeRef.current.src = getPdfUrl(viewerPdf, page); }, 50);
    }
  };

  const copyAnswer = () => {
    navigator.clipboard.writeText(answerText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const loadTables = async (pdfName) => {
    if (!pdfName) return;
    try {
      setTablesLoading(true);
      setExpandedTable(null);
      const response = await axios.get(`${API}/tables/${encodeURIComponent(pdfName)}`);
      setTables(response.data.tables || []);
    } catch (err) {
      console.error("Table load failed:", err);
      setTables([]);
    } finally {
      setTablesLoading(false);
    }
  };

  // ── Download helpers ──────────────────────────────────────────
  const buildDownloadText = () => {
    let txt = `Question: ${question}\n\n${answerText}`;
    if (parsedSources.length > 0) {
      txt += "\n\nSources:\n";
      parsedSources.forEach(s => { txt += `  ${s.pdf} — Page ${s.page}\n`; });
    }
    return txt;
  };

  const downloadTxt = () => {
    const blob = new Blob([buildDownloadText()], { type: "text/plain;charset=utf-8" });
    saveAs(blob, `${question.slice(0, 40).replace(/[^a-z0-9]/gi, "_")}.txt`);
  };

  const downloadDocx = async () => {
    const sourceParas = parsedSources.map(s =>
      new Paragraph({ children: [new TextRun({ text: `${s.pdf} — Page ${s.page}`, size: 20, color: "888888" })] })
    );
    const doc = new Document({
      sections: [{
        properties: {},
        children: [
          new Paragraph({ text: question, heading: HeadingLevel.HEADING_1 }),
          new Paragraph({ text: "" }),
          ...answerText.split("\n").map(line =>
            new Paragraph({ children: [new TextRun({ text: line, size: 22 })] })
          ),
          new Paragraph({ text: "" }),
          ...(parsedSources.length > 0 ? [
            new Paragraph({ text: "Sources", heading: HeadingLevel.HEADING_2 }),
            ...sourceParas,
          ] : []),
        ],
      }],
    });
    const blob = await Packer.toBlob(doc);
    saveAs(blob, `${question.slice(0, 40).replace(/[^a-z0-9]/gi, "_")}.docx`);
  };

  const downloadPdf = () => {
    const win = window.open("", "_blank");
    win.document.write(`
      <html><head><title>${question}</title>
      <style>
        body { font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #1a1a1a; }
        h1 { font-size: 18px; border-bottom: 2px solid #333; padding-bottom: 8px; margin-bottom: 20px; }
        pre { white-space: pre-wrap; font-family: inherit; font-size: 14px; }
        .sources { margin-top: 24px; padding-top: 12px; border-top: 1px solid #ccc; font-size: 12px; color: #555; }
      </style></head><body>
      <h1>${question}</h1>
      <pre>${answerText}</pre>
      ${parsedSources.length > 0 ? `<div class="sources"><strong>Sources:</strong><br>${parsedSources.map(s => `${s.pdf} — Page ${s.page}`).join("<br>")}</div>` : ""}
      </body></html>
    `);
    win.document.close();
    setTimeout(() => { win.print(); }, 500);
  };

  const askQuestion = async (overrideAgreement = null, overrideQuestion = null) => {
    const q = overrideQuestion || (overrideAgreement ? pendingQuestion : question);
    if (!q.trim()) return;
    try {
      setLoading(true);
      setAwaitingSelection(false);
      setAgreementOptions([]);
      setAnswer("");
      setConfidence(0);
      setParsedSources([]);
      setCopied(false);

      const payload = { question: q };
      if (overrideAgreement)    payload.agreement = overrideAgreement;
      else if (pinnedAgreement) payload.agreement = pinnedAgreement;

      const response = await axios.post(`${API}/ask`, payload);
      const data = response.data;

      if (data.requires_selection) {
        setPendingQuestion(q);
        setAgreementOptions(data.agreements);
        setAwaitingSelection(true);
        return;
      }

      setAnswer(data.answer);
      setConfidence(data.confidence || 0);
      const { sources } = parseAnswer(data.answer);
      setParsedSources(sources);
      saveToHistory(q, data.answer, data.source_pdf);

      if (data.source_pdf) {
        setViewerPdf(data.source_pdf);
        setCitedPages(data.cited_pages || []);
        setCitedIndex(0);
        const page = data.source_page || 1;
        setViewerPage(page);
        setTimeout(() => {
          if (iframeRef.current) {
            iframeRef.current.src = "";
            setTimeout(() => { iframeRef.current.src = getPdfUrl(data.source_pdf, page); }, 50);
          }
        }, 100);
      }

      setTimeout(() => {
        answerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 150);

    } catch (err) {
      console.error(err);
      setAnswer("Failed to connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  const selectAgreement = (pdfName) => {
    setAwaitingSelection(false);
    setAgreementOptions([]);
    setPinnedAgreement(pdfName);
    setViewerPdf(pdfName);
    setViewerPage(1);
    setCitedPages([]);
    setCitedIndex(0);
    setTimeout(() => {
      if (iframeRef.current) {
        iframeRef.current.src = "";
        setTimeout(() => { iframeRef.current.src = getPdfUrl(pdfName, 1); }, 50);
      }
    }, 100);
  };

  const searchKeyword = async () => {
    if (!agreement) return;
    try {
      const response = await axios.get(`${API}/keyword-search`, { params: { keyword, agreement } });
      setMatches(response.data.matches);
    } catch (err) { console.error(err); }
  };

  const searchGlobal = async () => {
    if (!globalKeyword.trim()) return;
    try {
      const response = await axios.get(`${API}/keyword-search-all`, { params: { keyword: globalKeyword } });
      setGlobalResults(response.data.results || []);
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    axios.get(`${API}/agreements`)
      .then((r) => {
        const pdfs = r.data?.agreements || [];
        setAgreements(pdfs);
        if (pdfs.length > 0) setAgreement(pdfs[0]);
      })
      .catch((e) => console.error("Agreement load failed:", e));
  }, []);

  useEffect(() => {
    if (viewerPdf) loadTables(viewerPdf);
    else setTables([]);
  }, [viewerPdf]);

  const shortName = (name) => name.replace(".pdf","").replace(".PDF","");
  const { text: answerText } = parseAnswer(answer);

  const filteredHistory = historySearch.trim()
    ? history.filter(e =>
        e.question.toLowerCase().includes(historySearch.toLowerCase()) ||
        (e.pdf && e.pdf.toLowerCase().includes(historySearch.toLowerCase()))
      )
    : history;

  return (
    <div className={`app ${darkMode ? "dark" : "light"}`}>

      <aside className="sidebar">
        <div className="logo-card">
          <div className="logo-icon">⚖️</div>
          <div>
            <h2>Legal RAG</h2>
            <p>Assistant</p>
          </div>
        </div>

        <div className="menu">
          <div className={`menu-item ${activeTab === "ask" ? "active" : ""}`} onClick={() => setActiveTab("ask")}>
            Ask Question
          </div>
          <div className={`menu-item ${activeTab === "history" ? "active" : ""}`} onClick={() => setActiveTab("history")}>
            History
            {history.length > 0 && <span className="history-badge">{history.length}</span>}
          </div>
          <div className={`menu-item ${activeTab === "bookmarks" ? "active" : ""}`} onClick={() => setActiveTab("bookmarks")}>
            Saved
            {bookmarks.length > 0 && <span className="history-badge">{bookmarks.length}</span>}
          </div>
        </div>

        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? "☀️ Light" : "🌙 Dark"}
        </button>

        <div className="about-card">
          <h3>About</h3>
          <p>Query telecom MSAs and get grounded answers with citations.</p>
        </div>
      </aside>

      <div className="split-layout">
        <div className="qa-panel">

          {/* ── History tab ── */}
          {activeTab === "history" && (
            <div>
              <div className="header">
                <h1>History</h1>
                <p>Your recent questions</p>
              </div>
              <input
                type="text"
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                placeholder="Search history..."
                style={{ marginBottom: "14px" }}
              />
              {filteredHistory.length === 0 ? (
                <div className="card">
                  <div className="empty-state">
                    <div className="empty-state-icon">📋</div>
                    <p>{historySearch ? "No matching history" : "No history yet"}</p>
                  </div>
                </div>
              ) : (
                <>
                  <button onClick={clearHistory} style={{ background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.35)", marginBottom: "14px" }}>
                    Clear All
                  </button>
                  {filteredHistory.map((entry) => (
                    <div key={entry.id} className="history-item" onClick={() => restoreFromHistory(entry)}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div className="history-question">{entry.question}</div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const updated = history.filter(h => h.id !== entry.id);
                            setHistory(updated);
                            localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
                          }}
                          style={{
                            margin: 0, padding: "2px 8px", fontSize: "10px",
                            background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)",
                            color: "#ef4444", borderRadius: "4px", flexShrink: 0, marginLeft: "8px",
                          }}
                        >✕</button>
                      </div>
                      <div className="history-meta">
                        {entry.pdf && <span className="history-pdf">📄 {shortName(entry.pdf)}</span>}
                        <span className="history-time">{entry.timestamp}</span>
                      </div>
                      <div className="history-preview">{entry.answer.slice(0, 120)}...</div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {/* ── Bookmarks tab ── */}
          {activeTab === "bookmarks" && (
            <div>
              <div className="header">
                <h1>Saved</h1>
                <p>Your bookmarked clauses</p>
              </div>
              {bookmarks.length === 0 ? (
                <div className="card">
                  <div className="empty-state">
                    <div className="empty-state-icon">⭐</div>
                    <p>No saved clauses yet. Click the star on any answer to save it.</p>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    onClick={() => { setBookmarks([]); localStorage.removeItem(BOOKMARK_KEY); }}
                    style={{ background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.35)", marginBottom: "14px" }}
                  >
                    Clear All
                  </button>
                  {bookmarks.map((entry) => (
                    <div key={entry.id} className="history-item" onClick={() => restoreFromHistory(entry)}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div className="history-question">⭐ {entry.question}</div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const updated = bookmarks.filter(b => b.id !== entry.id);
                            setBookmarks(updated);
                            localStorage.setItem(BOOKMARK_KEY, JSON.stringify(updated));
                          }}
                          style={{
                            margin: 0, padding: "2px 8px", fontSize: "10px",
                            background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)",
                            color: "#ef4444", borderRadius: "4px", flexShrink: 0, marginLeft: "8px",
                          }}
                        >✕</button>
                      </div>
                      <div className="history-meta">
                        {entry.pdf && <span className="history-pdf">📄 {shortName(entry.pdf)}</span>}
                        <span className="history-time">{entry.timestamp}</span>
                      </div>
                      <div className="history-preview">{entry.answer.slice(0, 120)}...</div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {/* ── Ask tab ── */}
          {activeTab === "ask" && (
            <>
              <div className="header">
                <h1>Legal RAG Assistant</h1>
                <p>Ask questions about your telecom agreements</p>
              </div>

              <div className="card">
                <h2>Ask a Question</h2>
                <textarea
                  value={question}
                  onChange={(e) => {
                    setQuestion(e.target.value);
                    setAwaitingSelection(false);
                    setAgreementOptions([]);
                    setAnswer("");
                    setConfidence(0);
                    setParsedSources([]);
                  }}
                  placeholder="e.g. State the clause for confidentiality in the Topaz agreement"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) askQuestion();
                  }}
                />
                <button onClick={() => askQuestion()} disabled={loading}>
                  {loading ? "Thinking…" : "Ask"}
                </button>
              </div>

              {pinnedAgreement && (
                <div className="pinned-agreement-bar">
                  <span>📌 Searching in: <strong>{shortName(pinnedAgreement)}</strong></span>
                  <button className="clear-pin-btn" onClick={() => { setPinnedAgreement(null); setViewerPdf(null); setCitedPages([]); setTables([]); }}>
                    Clear ✕
                  </button>
                </div>
              )}

              {awaitingSelection && (
                <div className="card">
                  <h2>Multiple agreements found — please select one</h2>
                  <p style={{ color: "var(--text-muted)", marginBottom: "16px", fontSize: "13px" }}>
                    Your question matches more than one agreement. Click the one you want to search.
                  </p>
                  <div className="agreement-selection-grid">
                    {agreementOptions.map((opt) => (
                      <div key={opt.pdf_name} className="agreement-option-card" onClick={() => selectAgreement(opt.pdf_name)}>
                        <h3>{opt.display_name}</h3>
                        {opt.agreement_date && <p className="agreement-date">{opt.agreement_date}</p>}
                        <p className="agreement-filename">{opt.pdf_name}</p>
                        {opt.parties.length > 0 && (
                          <div className="agreement-parties">
                            <span>Parties</span>
                            <ul>{opt.parties.map((p, i) => <li key={i}>{p}</li>)}</ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Answer card */}
              <div className="card" ref={answerRef}>
                <h2>Answer</h2>
                <div className="answer-box">
                  {answerText ? (
                    <>
                      <div className="answer-actions">
                        <button onClick={copyAnswer} className="action-btn" style={{
                          background: copied ? "rgba(34,197,94,0.2)" : "rgba(255,255,255,0.08)",
                          border: copied ? "1px solid rgba(34,197,94,0.4)" : "1px solid var(--border-2)",
                          color: copied ? "var(--green)" : "var(--text-dim)",
                        }}>
                          {copied ? "✓ Copied" : "Copy"}
                        </button>
                        <button onClick={toggleBookmark} className="action-btn" style={{
                          background: isBookmarked ? "rgba(240,165,0,0.2)" : "rgba(255,255,255,0.08)",
                          border: isBookmarked ? "1px solid rgba(240,165,0,0.4)" : "1px solid var(--border-2)",
                          color: isBookmarked ? "var(--gold)" : "var(--text-dim)",
                        }}>
                          {isBookmarked ? "⭐ Saved" : "☆ Save"}
                        </button>
                        <button onClick={downloadTxt} className="action-btn">TXT</button>
                        <button onClick={downloadDocx} className="action-btn">DOCX</button>
                        <button onClick={downloadPdf} className="action-btn">PDF</button>
                      </div>

                      <pre>{answerText}</pre>

                      {confidence > 0 && (
                        <div className="confidence-card" style={{
                          borderColor: confidence >= 80 ? "rgba(34,197,94,0.3)" : confidence >= 50 ? "rgba(245,158,11,0.3)" : "rgba(239,68,68,0.3)",
                          background: confidence >= 80 ? "rgba(34,197,94,0.07)" : confidence >= 50 ? "rgba(245,158,11,0.07)" : "rgba(239,68,68,0.07)"
                        }}>
                          <div className="confidence-label">Confidence</div>
                          <div className="confidence-row">
                            <div className="confidence-track">
                              <div className="confidence-fill" style={{
                                width: `${confidence}%`,
                                background: confidence >= 80 ? "var(--green)" : confidence >= 50 ? "var(--amber)" : "var(--red)"
                              }} />
                            </div>
                            <span className="confidence-pct" style={{
                              color: confidence >= 80 ? "var(--green)" : confidence >= 50 ? "var(--amber)" : "var(--red)"
                            }}>{confidence}%</span>
                          </div>
                        </div>
                      )}

                      {parsedSources.length > 0 && (
                        <div className="sources-section">
                          <div className="sources-label">Sources</div>
                          {parsedSources.map((s, i) => (
                            <div key={i} className="source-card" onClick={() => {
                              const page = parseInt(s.page);
                              if (!isNaN(page)) { setViewerPdf(s.pdf); jumpToPage(page); }
                            }}>
                              <div className="source-card-pdf">📄 {shortName(s.pdf)}</div>
                              <div className="source-card-meta">
                                <span className="source-card-path">{s.pdf}</span>
                                <span className="source-card-page">Page {s.page}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">⚖️</div>
                      <p>Your answer will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <h2>Keyword Search</h2>
                <div className="keyword-row">
                  <select value={agreement} onChange={(e) => setAgreement(e.target.value)}>
                    {agreements.length === 0
                      ? <option value="">Loading…</option>
                      : agreements.map((item) => <option key={item} value={item}>{shortName(item)}</option>)
                    }
                  </select>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && searchKeyword()}
                    placeholder="termination"
                  />
                  <button onClick={searchKeyword}>Search</button>
                </div>
              </div>

              {matches.length > 0 && (
                <div className="card">
                  <h2>Results ({matches.length})</h2>
                  {matches.map((match, i) => (
                    <div key={i} className="keyword-result">
                      <h4>Page {match.page_number}</h4>
                      {match.heading && <p>{match.heading}</p>}
                      <div dangerouslySetInnerHTML={{
                        __html: match.snippet.replaceAll("<<<HIGHLIGHT>>>","<mark>").replaceAll("<<<END>>>","</mark>")
                      }} />
                    </div>
                  ))}
                </div>
              )}

              <div className="card">
                <h2>Global Search</h2>
                <div className="keyword-row">
                  <input
                    type="text"
                    value={globalKeyword}
                    onChange={(e) => setGlobalKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && searchGlobal()}
                    placeholder="e.g. indemnification"
                    style={{ flex: 3 }}
                  />
                  <button onClick={searchGlobal} style={{ marginTop: 0 }}>Search All</button>
                </div>
              </div>

              {globalResults.length > 0 && (
                <div className="card">
                  <h2>
                    {globalResults.reduce((a, g) => a + g.count, 0)} matches across {globalResults.length} agreements
                  </h2>
                  {globalResults.map((group) => (
                    <div key={group.pdf_name} className="global-result-group">
                      <div className="global-result-header">
                        📄 {shortName(group.pdf_name)}
                        <span className="global-result-count">{group.count}</span>
                      </div>
                      {group.matches.map((match, i) => (
                        <div key={i} className="keyword-result">
                          <h4>Page {match.page_number}</h4>
                          {match.heading && <p>{match.heading}</p>}
                          <div dangerouslySetInnerHTML={{
                            __html: match.snippet.replaceAll("<<<HIGHLIGHT>>>","<mark>").replaceAll("<<<END>>>","</mark>")
                          }} />
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {/* Tables card — auto-loads when PDF opens */}
              {(tablesLoading || tables.length > 0) && (
                <div className="card">
                  <h2>Tables {tables.length > 0 ? `(${tables.length})` : ""}</h2>
                  {tablesLoading ? (
                    <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>Loading tables…</p>
                  ) : (
                    tables.map((table, i) => (
                      <div key={i} style={{ marginBottom: "10px" }}>
                        <div
                          style={{
                            display: "flex", justifyContent: "space-between", alignItems: "center",
                            padding: "8px 12px", background: "var(--surface-2)", borderRadius: "var(--radius-sm)",
                            cursor: "pointer", fontSize: "12px", fontWeight: 600, color: "var(--text-dim)",
                            border: "1px solid var(--border)",
                          }}
                          onClick={() => setExpandedTable(expandedTable === i ? null : i)}
                        >
                          <span>📊 Page {table.page} — Table {table.table_index}</span>
                          <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
                            {table.row_count} rows × {table.col_count} cols {expandedTable === i ? "▲" : "▼"}
                          </span>
                        </div>
                        {expandedTable === i && (
                          <div style={{ overflowX: "auto", marginTop: "6px" }}>
                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", color: "var(--text)" }}>
                              {table.headers.length > 0 && (
                                <thead>
                                  <tr>
                                    {table.headers.map((h, j) => (
                                      <th key={j} style={{
                                        padding: "6px 10px", background: "var(--accent-dim)",
                                        border: "1px solid var(--border-2)", textAlign: "left",
                                        fontWeight: 600, color: "var(--accent)", whiteSpace: "nowrap",
                                      }}>{h || "—"}</th>
                                    ))}
                                  </tr>
                                </thead>
                              )}
                              <tbody>
                                {table.rows.map((row, ri) => (
                                  <tr key={ri} style={{ background: ri % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
                                    {row.map((cell, ci) => (
                                      <td key={ci} style={{
                                        padding: "5px 10px", border: "1px solid var(--border)", verticalAlign: "top",
                                      }}>{cell || "—"}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <div className="pdf-panel">
          {viewerPdf ? (
            <>
              <div className="pdf-toolbar">
                <span className="pdf-name">📄 {shortName(viewerPdf)}</span>
                <span className="pdf-page-indicator">Page {viewerPage}</span>
                {citedPages.length > 0 && (
                  <div className="cited-nav">
                    <span>Cited:</span>
                    {citedPages.map((p, i) => (
                      <button
                        key={i}
                        className={`cited-page-btn ${i === citedIndex ? "active-cited" : ""}`}
                        onClick={() => { setCitedIndex(i); jumpToPage(p); }}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <iframe ref={iframeRef} src={getPdfUrl(viewerPdf, viewerPage)} className="pdf-iframe" title="PDF Viewer" />
            </>
          ) : (
            <div className="pdf-empty">
              <div className="pdf-empty-icon">📄</div>
              <p>Select an agreement to view the PDF here</p>
              <p className="pdf-empty-sub">The document will open automatically when you pick an agreement. Pages cited in answers will be highlighted.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;