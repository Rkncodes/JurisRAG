from openai import AzureOpenAI
from dotenv import load_dotenv
from app.config import DEBUG
from app.config import VERBOSE
from app.ingestion.retriever import collection
import os
import httpx

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    http_client=httpx.Client(verify=False)
)

def get_neighbor_chunks(metadata):

    if (
        "document_id" not in metadata
        or
        "chunk_id" not in metadata
    ):
        return []

    document_id = metadata["document_id"]
    chunk_id = metadata["chunk_id"]

    print("\nTOP CHUNK")
    print(metadata["heading"])
    print("CHUNK ID:", chunk_id)
    print("\nFULL METADATA")
    print(metadata)

    neighbor_ids = [
    chunk_id - 2,
    chunk_id - 1,
    chunk_id,
    chunk_id + 1,
    chunk_id + 2,
]

    neighbors = []

    results = collection.get(
        where={
            "document_id": document_id
        },
        include=["documents", "metadatas"]
    )

    docs = results["documents"]
    metas = results["metadatas"]

    for doc, meta in zip(docs, metas):

        if meta.get("chunk_id") in neighbor_ids:

            neighbors.append(
                {
                    "chunk": doc,
                    "metadata": meta
                }
            )

    neighbors.sort(
        key=lambda x: x["metadata"]["chunk_id"]
    )
    
    if DEBUG:
     print("\nNEIGHBOR CHUNKS FOUND")

     for n in neighbors:
      print(
        f"Chunk ID: {n['metadata']['chunk_id']} | "
        f"Page: {n['metadata']['page_number']}"
    )

    return neighbors

def generate_answer(question, ranked_results):

    top_chunks = ranked_results[:10]
    
    if VERBOSE: 

      print("\n\nRETRIEVED CHUNKS\n")

      for i, item in enumerate(top_chunks, start=1):

        print(f"\nCHUNK {i}")

        print(
            f"{item['metadata']['pdf_name']} | "
            f"Page {item['metadata']['page_number']}"
        )

        print("-" * 80)

        print(item["chunk"])

        print("-" * 80)

    if not top_chunks:
      return "I don't know anything about that from the provided documents."

    if DEBUG:

        print("\nTOP CHUNKS SENT TO LLM\n")

        for i, item in enumerate(top_chunks, start=1):
            print(
                f"{i}. "
                f"{item['metadata']['pdf_name']} | "
                f"Page {item['metadata']['page_number']} | "
                f"Score {item['score']}"
            )

        print("\nSOURCE CANDIDATES:")

        for i, item in enumerate(top_chunks, start=1):
            print(
                f"{i}. "
                f"{item['metadata']['pdf_name']} | "
                f"Page {item['metadata']['page_number']}"
            )

    expanded_chunks = []

    seen = set()

    for item in top_chunks:

        neighbors = get_neighbor_chunks(
            item["metadata"]
        )

        for neighbor in neighbors:

            key = (
                neighbor["metadata"]["document_id"],
                neighbor["metadata"]["chunk_id"]
            )

            if key not in seen:

                seen.add(key)

                expanded_chunks.append(
                    neighbor
                )

    chunks = [
        item["chunk"]
        for item in expanded_chunks
    ]

    metadata = [
        item["metadata"]
        for item in expanded_chunks
    ]
    
    if DEBUG:
     print(f"\nOriginal chunks: {len(top_chunks)}")
     print(f"Expanded chunks: {len(expanded_chunks)}")

    if DEBUG:
        print("\nQUESTION:")
        print(question)

    if VERBOSE:

     print("\nCHUNKS SENT TO LLM\n")

     for i, chunk in enumerate(chunks, start=1):

        print(f"\nCHUNK {i}")

        print(
            f"PDF: {metadata[i-1]['pdf_name']} | "
            f"Page: {metadata[i-1]['page_number']}"
        )

        print(chunk)

        print("=" * 100)

    if DEBUG:
        print("\n" + "=" * 80)

    context_parts = []

    chunk_map = {}

    for i, chunk in enumerate(chunks, start=1):

         chunk_id = f"CHUNK_{i:03d}"

         chunk_map[chunk_id] = metadata[i - 1]

         context_parts.append(
            f"""
{chunk_id}

CONTENT:
{chunk}
"""
        )

    context = "\n\n".join(context_parts)

    if DEBUG:
     print("\nTEST CHUNK MAP:")
     print(chunk_map["CHUNK_001"])

    prompt = f"""
You are a Legal Document Assistant.

IMPORTANT RULES:

1. Answer ONLY using the provided context.

2. When answering factual questions, provide the exact wording from the document whenever possible.

3. Do NOT use outside knowledge.

4. Do NOT make assumptions.

5. Do NOT infer facts.

6. If neither the answer nor a matching heading/section title
is present in the context, respond EXACTLY:

I don't know anything about that from the provided documents.

Information may appear inside tables, lists, OCR text, or poorly formatted text.

If the answer can be directly determined from the provided context, extract it even when the formatting is broken.

Do not require perfectly formatted tables.

Use nearby values and row structure when identifying quantities, item names, clause numbers, or document fields.

7. After your answer, write:

USED_CHUNKS:
CHUNK_XXX
CHUNK_YYY

List every chunk that directly supports the answer.

Only use chunk IDs that appear in the provided context.

Do not invent chunk IDs.

8. If the user asks for:

- a section
- a clause
- obligations
- responsibilities
- definitions
- terms
- conditions
- provisions
- schedules
- annexures
- agreement contents
- policy contents
- contract contents

then return the complete relevant text available in the provided context.

If the user's question matches or closely resembles a section title,
clause title, heading, subsection title, schedule title,
annexure title, policy title, or contract heading present in the context:

treat the question as a request for the contents of that section.

Return the full text associated with that heading.

Do NOT require the heading to contain a formal definition.

Do NOT summarize, shorten, paraphrase, compress, or omit sub-clauses.

Include all numbered clauses, sub-clauses, bullet points, and items available in the retrieved context.

Only provide a summary, analysis, interpretation, explanation, comparison, or simplification when the user explicitly asks for:

- a summary
- an analysis
- an explanation
- an interpretation
- key points
- highlights
- a simplified version
- a comparison

If the user explicitly asks for an explanation,summarise, summarisation, interpretation, analysis, or simplification:

1. First provide the relevant clause(s) from the document.

2. Then provide a separate section titled:

EXPLANATION

3. Explain the clause in plain English using only information present in the provided context.

4. Break the explanation into logical headings and bullet points wherever appropriate.

5. Add blank lines between sections for readability.

6. Describe:
   - what the clause means
   - what obligations it creates
   - what rights it grants
   - what consequences follow
   - any deadlines, payment periods, notice periods,
     percentages, penalties, service credits,
     termination rights, or monetary amounts
     explicitly mentioned in the clause

7. Do not introduce facts that are not supported by the context.Focus on the specific contents of the clause.

Do not provide generic contract explanations.

Reference the actual obligations, timelines,
numbers, percentages, conditions, and consequences
present in the retrieved text.

8. After USED_CHUNKS, add one line:

CONFIDENCE: X%

Where X is your honest estimate (0-100) of how completely
the provided context answered the question.
- 90-100%: full clause text found, complete answer
- 70-89%: most of the clause found, minor gaps
- 50-69%: partial clause found, some content missing
- Below 50%: very little relevant content found

Only base this on what is actually in the context.

8. Do not merely repeat or lightly paraphrase the clause text.

9. Use the following style whenever appropriate:

EXPLANATION

Meaning:
...

Key Obligations:
...

Rights:
...

Consequences:
...

Exceptions:
...

CONTEXT:

{context}

QUESTION:

{question}
"""

    if DEBUG:

        print("\nRERANKED SOURCES:\n")

        for i, meta in enumerate(metadata):
            print(
                f"{i + 1}. "
                f"{meta['pdf_name']} | "
                f"Page {meta['page_number']}"
            )
    
    if VERBOSE:
     print("\nPROMPT SENT TO GPT\n")
     print(prompt)
    
    
    print("\n" + "=" * 100)
    print("CONTEXT SENT TO GPT")
    print("=" * 100)
    print(context)
    print("=" * 100)
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {
                "role": "system",
                "content": "You are a legal document assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1500,
        temperature=0,
        top_p=1,
        seed=42
    )
    print("\nCONTEXT LENGTH:")
    print(len(context))
    
    print("\nQUESTION:")
    print(question)

    answer = response.choices[0].message.content.strip()
    if VERBOSE:
     print("\nRAW LLM RESPONSE\n")
     print(answer)
     print("=" * 100)

    best_source = metadata[0]

    used_chunk_ids = []

    if "USED_CHUNKS:" in answer:

      used_chunks_text = answer.split(
        "USED_CHUNKS:"
    )[1]

      used_chunk_ids = [
        line.strip()
        for line in used_chunks_text.splitlines()
        if line.strip().startswith("CHUNK_")
    ]

      if used_chunk_ids:

         used_sources = []

         for chunk_id in used_chunk_ids:

            if chunk_id in chunk_map:

                used_sources.append(
                    chunk_map[chunk_id]
                )

         if used_sources:

            best_source = used_sources[0]

            unique_sources = []

            for source in used_sources:

              if source not in unique_sources:
                 unique_sources.append(source)

         print("\nUSED SOURCES:")

         for source in used_sources:

            print(
                source["pdf_name"],
                source["page_number"]
            )

         print("\nCITATION SOURCE:")
         print(best_source)

    if answer.startswith(
    "I don't know anything about that from the provided documents."
):
     return "I don't know anything about that from the provided documents."

    if DEBUG:
        print("\nFINAL SOURCE:")
        print(
            f"{best_source.get('pdf_name')} | "
            f"Page {best_source.get('page_number')}"
        )
    sources_text = ""

    if 'unique_sources' in locals():

        for source in unique_sources:

            sources_text += (
                f"PDF Name : {source.get('pdf_name', 'Unknown')}\n"
                f"Page No  : {source.get('page_number', 'Unknown')}\n"
                f"PDF Path : {source.get('pdf_path', 'Unknown')}\n\n"
        )

    else:

       sources_text = (
          f"PDF Name : {best_source.get('pdf_name', 'Unknown')}\n"
          f"Page No  : {best_source.get('page_number', 'Unknown')}\n"
          f"PDF Path : {best_source.get('pdf_path', 'Unknown')}\n"
        )

    return f"""
{answer}

SOURCES USED

{sources_text}
"""