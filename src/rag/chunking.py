from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.schemas import Document, Chunk


def chunk_document(
    document: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,       # target size per chunk, in characters
        chunk_overlap=chunk_overlap, # characters shared between consecutive chunks
        separators=["\n\n", "\n", ". ", " ", ""],  # split priority order
    )

    raw_chunks = splitter.split_text(document.raw_text)

    chunks = []
    for i, text in enumerate(raw_chunks):
        chunks.append(
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
        )
    return chunks