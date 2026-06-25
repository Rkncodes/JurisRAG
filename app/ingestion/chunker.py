from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


def split_into_sections(text):

    def looks_like_heading(line):

        words = line.split()

        if len(words) > 12:
            return False

        lower = line.lower()

        sentence_indicators = [
            "shall",
            "will",
            "may",
            "must",
            "should",
            "means",
            "includes",
            "include",
            "responsible",
            "required"
        ]

        if any(word in lower for word in sentence_indicators):
            return False

        return True

    lines = text.split("\n")

    sections = []

    current_heading = None
    current_content = []
    current_page    = 1

    numbered_heading_pattern = re.compile(
        r"^\d+(?:\.\d+)*\.?\s+[A-Z].+$"
    )

    caps_heading_pattern = re.compile(
        r"^[A-Z][A-Z\s&\-]{3,}$"
    )

    article_heading_pattern = re.compile(
        r"^ARTICLE\s+\d+.*$",
        re.IGNORECASE
    )

    page_marker_pattern = re.compile(
        r"^<<<PAGE_(\d+)>>>$"
    )

    for line in lines:

        line = re.sub(
            r"^(\d+(?:\.\d+)+)([A-Z])",
            r"\1 \2",
            line
        )

        line = line.strip()

        if not line:
            continue

        # ── track page number from marker ─────────────────────────────
        page_match = page_marker_pattern.match(line)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        is_numbered_heading = (
            numbered_heading_pattern.match(line)
            and looks_like_heading(line)
        )

        is_caps_heading = caps_heading_pattern.match(line)

        is_article_heading = article_heading_pattern.match(line)

        if is_numbered_heading or is_caps_heading or is_article_heading:

            if current_heading:
                sections.append({
                    "heading":     current_heading,
                    "content":     "\n".join(current_content),
                    "page_number": current_page,
                })

            current_heading = line
            current_content = []
            # page_number at heading detection time

        else:
            current_content.append(line)

    if current_heading:
        sections.append({
            "heading":     current_heading,
            "content":     "\n".join(current_content),
            "page_number": current_page,
        })

    return sections


def chunk_pages(pages):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=500
    )

    chunks = []

    document_id = pages[0]["pdf_name"]
    pdf_name    = pages[0]["pdf_name"]
    pdf_path    = pages[0]["pdf_path"]

    chunk_counter = 0

    # ── STEP 1: merge all pages into one text stream ──────────────────
    # Insert page markers so section detector knows which page it's on.

    merged_lines = []

    for page in pages:
        merged_lines.append(
            f"<<<PAGE_{page['page_number']}>>>"
        )
        merged_lines.append(page["text"])

    merged_text = "\n".join(merged_lines)

    # ── STEP 2: split merged text into sections ───────────────────────

    sections = split_into_sections(merged_text)

    print(
        f"\nDOCUMENT: {pdf_name}"
        f"\nTOTAL SECTIONS FOUND: {len(sections)}"
    )

    if not sections:
        # fallback — store entire doc as one chunk per page
        for page in pages:
            chunk_counter += 1
            chunks.append({
                "chunk_text":  page["text"],
                "heading":     "",
                "pdf_name":    pdf_name,
                "page_number": page["page_number"],
                "pdf_path":    pdf_path,
                "document_id": document_id,
                "chunk_id":    chunk_counter,
            })
        return chunks

    # ── STEP 3: chunk each section ────────────────────────────────────

    for section in sections:

        heading     = section["heading"]
        page_number = section["page_number"]

        print(f"\nSECTION: {heading} | Page: {page_number}")

        section_text = (
            f"SECTION TITLE: {heading}\n\n"
            f"{section['content']}"
        )

        text_chunks = splitter.split_text(section_text)

        for chunk in text_chunks:

            chunk_counter += 1

            chunks.append({
                "chunk_text":  chunk,
                "heading":     heading,
                "pdf_name":    pdf_name,
                "page_number": page_number,
                "pdf_path":    pdf_path,
                "document_id": document_id,
                "chunk_id":    chunk_counter,
            })

    print(f"\nTotal chunks created: {len(chunks)}")

    return chunks