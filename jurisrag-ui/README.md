# ⚖️ JurisRAG

> Enterprise-grade Retrieval-Augmented Generation (RAG) system for intelligent legal document search and question answering.

JurisRAG is an AI-powered legal document intelligence platform that enables users to query complex legal agreements using natural language and receive accurate, citation-backed responses grounded entirely in the source documents.

Built during my internship at **Altius Infra**, the system was designed to assist legal teams in navigating lengthy telecom agreements by combining semantic search, structure-aware retrieval, OCR, reranking, and Azure OpenAI.

---

## ✨ Features

- 🔍 Semantic search across multiple legal agreements
- 📄 Citation-backed answers with page references
- 📑 Interactive PDF viewer with page navigation
- 📋 Automatic table extraction from legal documents
- 🧠 Structure-aware chunking preserving legal clause hierarchy
- 🎯 Cross-Encoder reranking for improved retrieval accuracy
- 🔎 Global keyword search across agreements
- 📚 Query history
- 🌗 Dark & Light themes
- 📈 Confidence scoring for retrieved responses
- 🖥️ Modern React-based user interface

---

# System Architecture

```text
                    Legal Agreements (PDFs)
                              │
                              ▼
                   PDF Extraction + OCR
                              │
                              ▼
               Structure-Aware Document Chunking
                              │
                              ▼
            Embeddings (BAAI/bge-small-en-v1.5)
                              │
                              ▼
                      Chroma Vector Store
                              │
                              ▼
                 Semantic Retrieval + Filtering
                              │
                              ▼
              Cross-Encoder Reranking (BGE)
                              │
                              ▼
                Azure OpenAI (GPT-4)
                              │
                              ▼
          Citation-backed Answer Generation
                              │
                              ▼
                     React Frontend
```

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | React, Vite |
| Backend | FastAPI |
| Vector Database | ChromaDB |
| Embeddings | BAAI/bge-small-en-v1.5 |
| Reranker | BGE Cross Encoder |
| OCR | Tesseract OCR |
| LLM | Azure OpenAI (GPT-4) |
| PDF Processing | PyMuPDF |
| Language | Python |

---

# Core Components

## Document Ingestion

- PDF parsing
- OCR fallback for scanned documents
- Automatic document classification
- Metadata extraction

---

## Structure-Aware Chunking

Unlike traditional fixed-size chunking, JurisRAG preserves legal document hierarchy by detecting:

- Section headings
- Numbered clauses
- Cross-page clause continuation
- Document structure

This significantly improves retrieval quality for legal documents.

---

## Semantic Retrieval

The retrieval pipeline consists of:

1. Query preprocessing
2. Agreement detection
3. Embedding generation
4. Vector similarity search
5. Metadata filtering
6. Cross-Encoder reranking
7. Context expansion

---

## Answer Generation

Retrieved context is passed to Azure OpenAI, which generates answers constrained strictly to the provided legal context.

Each response includes:

- Source agreement
- Page citations
- Confidence score

---

# Example Query

### Input

```text
What are Vodafone's termination obligations?
```

### Output

```text
The agreement specifies that Vodafone may terminate the contract
under the following conditions...

Source:
Vodafone Agreement
Page 47
```

---

# Project Structure

```text
JurisRAG/

├── app/
│   ├── api.py
│   ├── config.py
│   ├── models.py
│   ├── ingestion/
│   │     ├── chunker.py
│   │     ├── pdf_loader.py
│   │     ├── retriever.py
│   │     ├── reranker.py
│   │     ├── vector_store.py
│   │     └── table_extractor.py
│   │
│   └── llm/
│         └── llm.py
│
├── legal-rag-ui/
│
├── agreements/
│
└── chroma_db/
```

# Installation

Clone the repository:

```bash
git clone https://github.com/Rkncodes/legal-rag.git

cd legal-rag
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn app.api:app --reload
```

Run the frontend:

```bash
cd legal-rag-ui

npm install

npm run dev
```

---

# Future Improvements

- Hybrid Retrieval (BM25 + Dense Retrieval)
- Streaming Responses
- Role-based Authentication
- Multi-document comparison
- Legal clause summarization
- Agentic legal workflows
- Cloud deployment

---

# Author

**Rajvinder Kaur**

- GitHub: https://github.com/Rkncodes
- LinkedIn: https://www.linkedin.com/in/rajvinder-kaur-5a2442323/

---

## License

This project is intended for educational and portfolio purposes.