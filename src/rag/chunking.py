from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.schemas import Document, Chunk


def chunk_document(
    document: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    if document.file_type == "csv":
        lines = [line for line in document.raw_text.split("\n") if line.strip()]
        chunks = []
        for i, line in enumerate(lines):
            row_fields = {}
            for pair in line.split(" | "):
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
                        **row_fields,
                    },
                )
            )
        return chunks

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