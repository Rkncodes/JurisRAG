import chromadb
import re
from sentence_transformers import SentenceTransformer
from app.config import DEBUG
from app.ingestion.agreement_detector import detect_agreement


embedding_model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    "legal_documents"
)

def get_neighbor_chunks(metadata):

    pdf_name = metadata["pdf_name"]

    chunk_id = metadata["chunk_id"]

    print(
        "\nCHUNK ID TYPE:",
        type(chunk_id),
        "VALUE:",
        chunk_id
    )

    neighbors = collection.get(
        where={
            "pdf_name": pdf_name
        },
        include=[
            "documents",
            "metadatas"
        ]
    )

    expanded = []

    for doc, meta in zip(
        neighbors["documents"],
        neighbors["metadatas"]
    ):

        if abs(
            int(meta["chunk_id"]) -
            int(chunk_id)
        ) <= 1:

            expanded.append(
                (
                    doc,
                    meta
                )
            )

    return expanded

print(
    "Collection count:",
    collection.count()
)

# ── CHANGED: added force_agreement=None parameter ─────────────────────────
def retrieve(query, k=15, force_agreement=None):

    print("\nQUERY RECEIVED:", query)

    print(
        "COLLECTION COUNT:",
        collection.count()
    )

    def normalize_query(query):

        query = query.lower()

        query = query.replace(
            "master service agreement",
            ""
        )

        query = query.replace(
            "master services agreement",
            ""
        )

        query = query.replace(
            "msa",
            ""
        )

        query = query.replace(
            "what is the clause for",
            ""
        )

        query = query.replace(
            "what is",
            ""
        )

        return query.strip()

    query_for_search = normalize_query(
        query
    )

    print(
        "NORMALIZED QUERY:",
        query_for_search
    )

    query_embedding = embedding_model.encode(
        query_for_search,
        normalize_embeddings=True
    ).tolist()

    where_filter = None

    # ── CHANGED: force_agreement takes priority over detect_agreement ─────
    if force_agreement:

        where_filter = {
            "pdf_name": force_agreement
        }

        agreement_pdf = force_agreement

        print(
            f"\nFORCE AGREEMENT: {force_agreement}"
        )

    else:

        agreement_pdf = detect_agreement(
            query,
            collection
        )

        if agreement_pdf:

            where_filter = {
                "pdf_name": agreement_pdf
            }

            print(
                f"\nAGREEMENT DETECTED: {agreement_pdf}"
            )

    # ─────────────────────────────────────────────────────────────────────

    print("\n========== RETRIEVER DEBUG ==========")
    print("QUERY:", query)
    print("WHERE FILTER:", where_filter)
    print("====================================")

    print(
    "AGREEMENT PDF:",
    repr(agreement_pdf)
    )

    all_data = collection.get(
    include=["documents", "metadatas"]
    )

    all_docs = collection.get(
    include=["documents"]
)

    print("\nSEARCHING FOR NOTICE\n")

    for doc in all_docs["documents"]:

     if "notice" in doc.lower():

        print("\nFOUND NOTICE CHUNK\n")
        print(doc[:1000])
        break
     
     print("\nSEARCHING FOR CONFIDENTIALITY\n")

    for doc in all_docs["documents"]:

     if "confidential" in doc.lower():

        print("\nFOUND CONFIDENTIALITY CHUNK\n")
        print(doc[:1000])
        break

    for doc, meta in zip(
     all_data["documents"],
     all_data["metadatas"]
):

     if meta["pdf_name"] == "BSNL & Voda (IP)  MSA dated 20 Jan 2014- USO.pdf":

        if "notice" in doc.lower():

            print("\nFOUND NOTICE\n")
            print(meta)
            print(doc[:1000])

    print("\nSEARCHING FOR NOTICE CLAUSES\n")

    for doc, meta in zip(
     all_data["documents"],
     all_data["metadatas"]
):

      if (
         "notice" in doc.lower()
         or
         "communication" in doc.lower()
         or
         "notices" in doc.lower()
    ):

          print("\nFOUND\n")

          print(
            "PDF:",
            meta["pdf_name"]
        )

          print(
            "PAGE:",
            meta["page_number"]
        )

          print(
            doc[:500]
        )

    all_data = collection.get(
    include=["metadatas"]
)

    print("\nALL PDF NAMES IN CHROMA\n")

    pdfs = set()

    for meta in all_data["metadatas"]:

     pdfs.add(
        meta["pdf_name"]
    )

    for pdf in sorted(pdfs):

     print(repr(pdf))

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=50,
        where=where_filter,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    if not results["metadatas"][0]:

        print(
            "\nNO RESULTS FOUND FOR FILTER\n"
        )

        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    print("\nFIRST METADATA ENTRY\n")
    print(results["metadatas"][0][0])

    print("\nFIRST METADATA ENTRY\n")
    print(results["metadatas"][0][0])

    print("\nFULL METADATA OBJECT\n")
    print(results["metadatas"][0][0])

    print("\nAVAILABLE METADATA KEYS\n")
    print(
    results["metadatas"][0][0].keys()
    )

    print("\nAVAILABLE METADATA KEYS\n")
    print(
        results["metadatas"][0][0].keys()
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    print("\nTOP PDFS RETURNED\n")

    for meta in metadatas[:10]:

        print(
            meta.get("pdf_name")
        )

    print("\nRAW RETRIEVAL RESULTS\n")

    for rank, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances),
        start=1
    ):
        print(
            f"{rank}. "
            f"{meta['pdf_name']} | "
            f"Page {meta['page_number']} | "
            f"Distance {dist}"
        )

    boosted = []

    for doc, meta, dist in zip(
        documents,
        metadatas,
        distances
    ):

        score = -dist

        pdf_name = meta.get(
            "pdf_name",
            ""
        ).lower()

        query_lower = query.lower()

        if pdf_name in query_lower:

            score += 20

            print(
                f"PDF BOOST APPLIED -> "
                f"{pdf_name}"
            )

        heading = meta.get(
            "heading",
            ""
        ).lower()

        clean_heading = re.sub(
            r"^\d+(\.\d+)*\s*",
            "",
            heading
        ).strip()

        if clean_heading:

            if (
                clean_heading in query_lower
                or
                query_lower in clean_heading
            ):
                score += 5

                print(
                    f"HEADING BOOST APPLIED -> "
                    f"{heading}"
                )

        boosted.append(
            (
                score,
                doc,
                meta,
                dist
            )
        )

    boosted.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    expanded_docs = []
    expanded_meta = []

    seen = set()

    for item in boosted[:5]:

        _, _, meta, _ = item

        neighbors = get_neighbor_chunks(
            meta
        )

        for doc, neighbor_meta in neighbors:

            key = (
                 neighbor_meta["pdf_name"],
                 neighbor_meta["chunk_id"]
             )

            if key in seen:
                continue

            seen.add(key)

            expanded_docs.append(doc)

            expanded_meta.append(
                   neighbor_meta
            )

    print("\nTOP 10 AFTER BOOSTING\n")

    for i, item in enumerate(
        boosted[:10],
        start=1
    ):
        print(
            f"{i}. "
            f"{item[2]['pdf_name']} | "
            f"Page {item[2]['page_number']}"
        )

    print("\nHEADING BOOST RESULTS\n")

    for rank, item in enumerate(
        boosted[:10],
        start=1
    ):
        print(
            f"{rank}. "
            f"{item[2].get('heading', '')}"
        )

    results["documents"][0] = expanded_docs

    results["metadatas"][0] = expanded_meta

    results["distances"][0] = [
        0
        for _ in expanded_docs
    ]

    print("\nPAGES RETURNED\n")

    pages = set()

    for meta in results["metadatas"][0]:

     pages.add(
        meta["page_number"]
    )

    print(
    sorted(pages)
)

    if DEBUG:

        print("\n" + "=" * 80)
        print(f"QUERY: {query}")
        print("=" * 80)
        print("\nBOOSTED RESULTS\n")

        for i in range(
            len(results["documents"][0])
        ):

            metadata = (
                results["metadatas"][0][i]
            )

            document = (
                results["documents"][0][i]
            )

            print(
                f"\nRank {i + 1}"
            )

            print(
                f"Distance: "
                f"{results['distances'][0][i]}"
            )

            print(
                f"PDF: "
                f"{metadata['pdf_name']}"
            )

            print(
                f"Page: "
                f"{metadata['page_number']}"
            )

            if "heading" in metadata:

                print(
                    f"Heading: "
                    f"{metadata['heading']}"
                )

            if "document_id" in metadata:

                print(
                    f"Document ID: "
                    f"{metadata['document_id']}"
                )

            if "chunk_id" in metadata:

                print(
                    f"Chunk ID: "
                    f"{metadata['chunk_id']}"
                )

            print(
                "\nTEXT PREVIEW:"
            )

            print(
                "-" * 40
            )

            preview = document[:500]

            print(preview)

            print(
                "-" * 40
            )

    return results