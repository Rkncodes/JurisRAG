import { useEffect, useState, useRef } from "react";
import axios from "axios";
import "./App.css";

const API = "http://127.0.0.1:8000";
const HISTORY_KEY = "legal-rag-history";

function App() {

  const [question, setQuestion]           = useState("");
  const [answer, setAnswer]               = useState("");
  const [keyword, setKeyword]             = useState("");
  const [matches, setMatches]             = useState([]);
  const [agreement, setAgreement]         = useState("");
  const [agreements, setAgreements]       = useState([]);
  const [loading, setLoading]             = useState(false);
  const [confidence, setConfidence]       = useState(0);

  // ambiguity
  const [awaitingSelection, setAwaitingSelection] = useState(false);
  const [agreementOptions, setAgreementOptions]   = useState([]);
  const [pendingQuestion, setPendingQuestion]     = useState("");

  // pinned agreement
  const [pinnedAgreement, setPinnedAgreement]     = useState(null);

  // PDF viewer
  const [viewerPdf, setViewerPdf]         = useState(null);
  const [viewerPage, setViewerPage]       = useState(1);
  const [citedPages, setCitedPages]       = useState([]);
  const [citedIndex, setCitedIndex]       = useState(0);
  const iframeRef                         = useRef(null);

  // history
  const [history, setHistory]             = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    } catch {
      return [];
    }
  });
  const [activeTab, setActiveTab]         = useState("ask");

  const saveToHistory = (q, a, pdf) => {
    const entry = {
      id: Date.now(),
      question: q,
      answer: a,
      pdf: pdf || null,
      timestamp: new Date().toLocaleString(),
    };
    const updated = [entry, ...history].slice(0, 50);
    setHistory(updated);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  };

  const restoreFromHistory = (entry) => {
    setQuestion(entry.question);
    setAnswer(entry.answer);
    setActiveTab("ask");
    if (entry.pdf) {
      setViewerPdf(entry.pdf);
      setViewerPage(1);
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = "";
          setTimeout(() => {
            iframeRef.current.src = getPdfUrl(entry.pdf, 1);
          }, 50);
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
      setTimeout(() => {
        iframeRef.current.src = getPdfUrl(viewerPdf, page);
      }, 50);
    }
  };

  const askQuestion = async (overrideAgreement = null) => {

    const q = overrideAgreement ? pendingQuestion : question;
    if (!q.trim()) return;

    try {
      setLoading(true);
      setAwaitingSelection(false);
      setAgreementOptions([]);
      setAnswer("");
      setConfidence(0);

      const payload = { question: q };
      if (overrideAgreement) payload.agreement = overrideAgreement;
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
            setTimeout(() => {
              iframeRef.current.src = getPdfUrl(data.source_pdf, page);
            }, 50);
          }
        }, 100);
      }

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
        setTimeout(() => {
          iframeRef.current.src = getPdfUrl(pdfName, 1);
        }, 50);
      }
    }, 100);
    askQuestion(pdfName);
  };

  const searchKeyword = async () => {
    if (!agreement) return;
    try {
      const response = await axios.get(`${API}/keyword-search`, {
        params: { keyword, agreement },
      });
      setMatches(response.data.matches);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    axios
      .get(`${API}/agreements`)
      .then((response) => {
        const pdfs = response.data?.agreements || [];
        setAgreements(pdfs);
        if (pdfs.length > 0) setAgreement(pdfs[0]);
      })
      .catch((error) => console.error("Agreement load failed:", error));
  }, []);

  return (
    <div className="app">

      <aside className="sidebar">
        <div className="logo-card">
          <div className="logo-icon">⚖️</div>
          <div>
            <h2>Legal RAG</h2>
            <p>Assistant</p>
          </div>
        </div>
        <div className="menu">
          <div
            className={`menu-item ${activeTab === "ask" ? "active" : ""}`}
            onClick={() => setActiveTab("ask")}
          >
            Ask Question
          </div>
          <div
            className={`menu-item ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            History {history.length > 0 && (
              <span className="history-badge">{history.length}</span>
            )}
          </div>
          <div className="menu-item">About</div>
        </div>
        <div className="about-card">
          <h3>About</h3>
          <p>
            Ask questions across telecom agreements
            and retrieve grounded answers with citations.
          </p>
        </div>
      </aside>

      <div className="split-layout">

        <div className="qa-panel">

          {/* HISTORY TAB */}
          {activeTab === "history" && (
            <div>
              <div className="header">
                <h1>History</h1>
                <p>Your recent questions and answers</p>
              </div>
              {history.length === 0 ? (
                <div className="card">
                  <div className="empty-state" style={{ minHeight: "120px" }}>
                    <p style={{ fontSize: "16px" }}>No history yet</p>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    onClick={clearHistory}
                    style={{
                      background: "rgba(239,68,68,0.2)",
                      border: "1px solid rgba(239,68,68,0.4)",
                      marginBottom: "16px",
                      padding: "8px 16px",
                      fontSize: "13px",
                    }}
                  >
                    Clear All
                  </button>
                  {history.map((entry) => (
                    <div
                      key={entry.id}
                      className="history-item"
                      onClick={() => restoreFromHistory(entry)}
                    >
                      <div className="history-question">{entry.question}</div>
                      <div className="history-meta">
                        {entry.pdf && (
                          <span className="history-pdf">
                            📄 {entry.pdf.replace(".pdf","").replace(".PDF","")}
                          </span>
                        )}
                        <span className="history-time">{entry.timestamp}</span>
                      </div>
                      <div className="history-preview">
                        {entry.answer.slice(0, 120)}...
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {/* ASK TAB */}
          {activeTab === "ask" && (
            <>
              <div className="header">
                <h1>Legal RAG Assistant</h1>
                <p>Ask questions about your legal agreements</p>
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
                  }}
                  placeholder="Type your legal question here..."
                />
                <button onClick={() => askQuestion()}>
                  {loading ? "Thinking..." : "Ask"}
                </button>
              </div>

              {pinnedAgreement && (
                <div className="pinned-agreement-bar">
                  <span>
                    📌 Searching in:{" "}
                    <strong>
                      {pinnedAgreement.replace(".pdf","").replace(".PDF","")}
                    </strong>
                  </span>
                  <button
                    className="clear-pin-btn"
                    onClick={() => {
                      setPinnedAgreement(null);
                      setViewerPdf(null);
                      setCitedPages([]);
                    }}
                  >
                    Clear ✕
                  </button>
                </div>
              )}

              {awaitingSelection && (
                <div className="card">
                  <h2>Multiple agreements found — please select one</h2>
                  <p style={{ color: "#93c5fd", marginBottom: "20px" }}>
                    Your question matches more than one agreement.
                    Click the one you want to search.
                  </p>
                  <div className="agreement-selection-grid">
                    {agreementOptions.map((opt) => (
                      <div
                        key={opt.pdf_name}
                        className="agreement-option-card"
                        onClick={() => selectAgreement(opt.pdf_name)}
                      >
                        <h3>{opt.display_name}</h3>
                        {opt.agreement_date && (
                          <p className="agreement-date">{opt.agreement_date}</p>
                        )}
                        <p className="agreement-filename">{opt.pdf_name}</p>
                        {opt.parties.length > 0 && (
                          <div className="agreement-parties">
                            <span>Parties:</span>
                            <ul>
                              {opt.parties.map((p, i) => (
                                <li key={i}>{p}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="card">
                <h2>Answer</h2>
                <div className="answer-box">
                  {answer ? (
                    <>
                      {confidence > 0 && (
                        <div className="confidence-bar">
                          <span>Confidence: {confidence}%</span>
                          <div className="confidence-track">
                            <div
                              className="confidence-fill"
                              style={{
                                width: `${confidence}%`,
                                background:
                                  confidence >= 80
                                    ? "#22c55e"
                                    : confidence >= 50
                                    ? "#f59e0b"
                                    : "#ef4444",
                              }}
                            />
                          </div>
                        </div>
                      )}
                      <pre>{answer}</pre>
                    </>
                  ) : (
                    <div className="empty-state">
                      ⚖️
                      <p>Your answer will appear here</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="card">
                <h2>Keyword Search</h2>
                <p style={{ marginBottom: "12px", color: "#93c5fd" }}>Agreement</p>
                <div className="keyword-row">
                  <select
                    value={agreement}
                    onChange={(e) => setAgreement(e.target.value)}
                  >
                    {agreements.length === 0 ? (
                      <option value="">Loading agreements...</option>
                    ) : (
                      agreements.map((item) => (
                        <option key={item} value={item}>
                          {item.replace(".pdf", "").replace(".PDF", "")}
                        </option>
                      ))
                    )}
                  </select>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="termination"
                  />
                  <button onClick={searchKeyword}>Search Keyword</button>
                </div>
              </div>

              <div className="card">
                <h2>Keyword Results ({matches.length})</h2>
                {matches?.map((match, index) => (
                  <div key={index} className="keyword-result">
                    <h4>Page {match.page_number}</h4>
                    {match.heading && <p>{match.heading}</p>}
                    <div
                      dangerouslySetInnerHTML={{
                        __html: match.snippet
                          .replaceAll("<<<HIGHLIGHT>>>", "<mark>")
                          .replaceAll("<<<END>>>", "</mark>"),
                      }}
                    />
                  </div>
                ))}
              </div>
            </>
          )}

        </div>

        {/* PDF viewer */}
        <div className="pdf-panel">
          {viewerPdf ? (
            <>
              <div className="pdf-toolbar">
                <span className="pdf-name">
                  📄 {viewerPdf.replace(".pdf","").replace(".PDF","")}
                </span>
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
              <iframe
                ref={iframeRef}
                src={getPdfUrl(viewerPdf, viewerPage)}
                className="pdf-iframe"
                title="PDF Viewer"
              />
            </>
          ) : (
            <div className="pdf-empty">
              <div className="pdf-empty-icon">📄</div>
              <p>Select an agreement to view the PDF here</p>
              <p className="pdf-empty-sub">
                The document will open automatically when you pick an agreement.
                Pages cited in answers will be highlighted.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;