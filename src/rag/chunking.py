from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.schemas import Document, Chunk


def chunk_document(
    document: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    # CSVs are structured, row-based data. Splitting by character count can merge multiple unrelated rows into one chunk, diluting the
    # embedding and hurting retrieval precision. Instead, each row (already a single line, from load_csv's row-per-line format)
    # becomes its own chunk — this preserves one fact per vector.
    if document.file_type == "csv":
        lines = [line for line in document.raw_text.split("\n") if line.strip()]
        chunks = []
        for i, line in enumerate(lines):
            row_fields = {}
            for pair in line.split(", "):
                if ": " in pair:
                    key, value = pair.split(": ", 1)
                    row_fields[key.strip()] = value.strip()

            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}_chunk_{i}",
                    doc_id=document.doc_id,
                    text=line,
                    chunk_index=i,
                    metadata={
                        "filename": document.filename,
                        "file_type": document.file_type,
                        **document.metadata,
                        **row_fields,   # adds status, owner, priority, task_id as real metadata
                    },
                )
            )
        return chunks

    # Prose documents (PDF, DOCX, TXT) still benefit from the recursive character splitter, since meaning spans sentences/paragraphs.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw_chunks = splitter.split_text(document.raw_text)

    return [
        Chunk(
            chunk_id=f"{document.doc_id}_chunk_{i}",
            doc_id=document.doc_id,
            text=text,
            chunk_index=i,
            metadata={
                "filename": document.filename,
                "file_type": document.file_type,
                **document.metadata,
            },
        )
        for i, text in enumerate(raw_chunks)
    ]