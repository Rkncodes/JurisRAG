from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.ingestion.reranker import rerank
from app.ingestion.retriever import retrieve
from app.llm.llm import generate_answer
from app.ingestion.retriever import collection
from app.ingestion.agreement_detector import (
    AGREEMENT_METADATA,
    FAMILY_KEYWORDS,
    DIRECT_PDF_KEYWORDS,
    normalize_query,
)
import re
import os

from app.models import (
    QuestionRequest,
    QuestionResponse,
    AgreementOption,
)

app = FastAPI(title="Legal RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Legal RAG API Running"}


# ── serve PDF files ───────────────────────────────────────────────────────

@app.get("/pdf/{pdf_name:path}")
def serve_pdf(pdf_name: str):

    results = collection.get(include=["metadatas"])
    pdf_path = None

    for meta in results["metadatas"]:
        if meta["pdf_name"] == pdf_name:
            pdf_path = meta.get("pdf_path")
            break

    if not pdf_path:
        raise HTTPException(status_code=404, detail=f"PDF not found: {pdf_name}")

    pdf_path = pdf_path.replace("\\", "/")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"File not found on disk: {pdf_path}")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={pdf_name}",
            "Access-Control-Allow-Origin": "*",
        }
    )


# ── routing helpers ───────────────────────────────────────────────────────

def get_matching_agreements(query: str) -> list[dict]:
    query_lower = normalize_query(query)

    sorted_keywords = sorted(DIRECT_PDF_KEYWORDS.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        if keyword in query_lower:
            pdf_name = DIRECT_PDF_KEYWORDS[keyword]
            for agreement in AGREEMENT_METADATA:
                if agreement["pdf_name"] == pdf_name:
                    print(f"\nDIRECT MATCH: '{keyword}' → {pdf_name}")
                    return [agreement]
            return []

    for family, keywords in FAMILY_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                family_agreements = [
                    a for a in AGREEMENT_METADATA
                    if a.get("family") == family
                ]
                print(f"\nFAMILY MATCH: '{kw}' → {family} ({len(family_agreements)} agreements)")
                return family_agreements

    print("\nNO MATCH → search all")
    return []


def is_direct_match(query: str) -> bool:
    query_lower = normalize_query(query)
    sorted_keywords = sorted(DIRECT_PDF_KEYWORDS.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in query_lower:
            return True
    return False


def build_agreement_options(matched: list[dict]) -> list[AgreementOption]:
    options = []
    for m in matched:
        options.append(
            AgreementOption(
                pdf_name=m["pdf_name"],
                display_name=m.get(
                    "display_name",
                    m["pdf_name"].replace(".pdf", "").replace(".PDF", ""),
                ),
                agreement_date=m.get("agreement_date", ""),
                parties=m.get("parties", []),
            )
        )
    return options


def extract_sources(answer: str) -> tuple[str | None, int | None, list[int]]:
    source_pdf  = None
    source_page = None
    cited_pages = []

    if "SOURCES USED" not in answer:
        return source_pdf, source_page, cited_pages

    sources_block = answer.split("SOURCES USED")[1]
    lines = sources_block.strip().splitlines()

    for line in lines:
        line = line.strip()
        if line.startswith("PDF Name"):
            pdf = line.split(":", 1)[-1].strip()
            if source_pdf is None:
                source_pdf = pdf
        elif line.startswith("Page No"):
            try:
                page = int(line.split(":", 1)[-1].strip())
                if source_page is None:
                    source_page = page
                if page not in cited_pages:
                    cited_pages.append(page)
            except ValueError:
                pass

    return source_pdf, source_page, cited_pages


def extract_confidence(answer: str) -> int:
    """Parse CONFIDENCE: X% from answer string."""
    if "CONFIDENCE:" not in answer:
        return 0
    try:
        line = [l for l in answer.splitlines() if "CONFIDENCE:" in l][0]
        val = re.search(r"(\d+)", line)
        return int(val.group(1)) if val else 0
    except:
        return 0


# ── /ask endpoint ─────────────────────────────────────────────────────────

@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):

    print("\nASK ENDPOINT HIT\n")
    print("QUESTION:", request.question)
    print("AGREEMENT:", request.agreement)

    if request.agreement:

        print(f"\nUSING PRE-SELECTED: {request.agreement}")

        retrieval_results = retrieve(
            request.question, k=20, force_agreement=request.agreement,
        )
        ranked_results = rerank(request.question, retrieval_results)

        if not ranked_results:
            return QuestionResponse(
                answer="I don't know anything about that from the provided documents."
            )

        answer = generate_answer(request.question, ranked_results)
        source_pdf, source_page, cited_pages = extract_sources(answer)
        confidence = extract_confidence(answer)

        return QuestionResponse(
            answer=answer,
            source_pdf=source_pdf,
            source_page=source_page,
            cited_pages=cited_pages,
            confidence=confidence,
        )

    matched = get_matching_agreements(request.question)
    direct  = is_direct_match(request.question)

    print(f"\nMATCHED: {len(matched)} | DIRECT: {direct}")
    for m in matched:
        print(" -", m["pdf_name"])

    if len(matched) >= 1 and not direct:
        print("\nSHOWING CARDS → requires_selection=True")
        return QuestionResponse(
            requires_selection=True,
            agreements=build_agreement_options(matched),
        )

    if len(matched) == 1 and direct:
        print(f"\nDIRECT SINGLE → {matched[0]['pdf_name']}")
        retrieval_results = retrieve(
            request.question, k=20, force_agreement=matched[0]["pdf_name"],
        )
    else:
        print("\nNO MATCH → search all")
        retrieval_results = retrieve(request.question, k=20)

    ranked_results = rerank(request.question, retrieval_results)

    if not ranked_results:
        return QuestionResponse(
            answer="I don't know anything about that from the provided documents."
        )

    answer = generate_answer(request.question, ranked_results)
    source_pdf, source_page, cited_pages = extract_sources(answer)
    confidence = extract_confidence(answer)

    return QuestionResponse(
        answer=answer,
        source_pdf=source_pdf,
        source_page=source_page,
        cited_pages=cited_pages,
        confidence=confidence,
    )


# ── existing endpoints ────────────────────────────────────────────────────

@app.get("/keyword-search")
def keyword_search(keyword: str, agreement: str):

    keyword = keyword.lower()
    results = collection.get(include=["documents", "metadatas"])
    matches = []

    for doc, meta in zip(results["documents"], results["metadatas"]):

        if agreement.lower() not in meta["pdf_name"].lower():
            continue

        doc_lower = doc.lower()

        if keyword not in doc_lower:
            continue

        index = doc_lower.find(keyword)
        start = max(0, index - 150)
        end   = min(len(doc), index + 150)
        snippet = " ".join(doc[start:end].split())
        snippet = re.sub(
            rf"(?i)({re.escape(keyword)})",
            r"<<<HIGHLIGHT>>>\1<<<END>>>",
            snippet,
        )

        matches.append({
            "page_number": meta["page_number"],
            "heading":     meta.get("heading", ""),
            "snippet":     snippet,
        })

    return {
        "keyword":   keyword,
        "agreement": agreement,
        "count":     len(matches),
        "matches":   matches,
    }


@app.get("/agreements")
def get_agreements():

    results = collection.get(include=["metadatas"])
    agreements = set()

    for meta in results["metadatas"]:
        agreements.add(meta["pdf_name"])

    return {"agreements": sorted(list(agreements))}