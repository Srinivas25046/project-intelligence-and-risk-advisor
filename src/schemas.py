from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str              # unique id, e.g. a generated UUID
    filename: str            # original filename, e.g. "project_proposal.pdf"
    file_type: str           # "pdf" | "docx" | "csv" | "txt"
    raw_text: str            # full extracted text content
    metadata: dict = field(default_factory=dict)   # e.g. {"num_pages": 12}


@dataclass
class Chunk:
    chunk_id: str             # unique id, e.g. "<doc_id>_chunk_3"
    doc_id: str               # which Document this chunk came from (traceability)
    text: str                 # the actual chunk content
    chunk_index: int          # position of this chunk within its source document
    metadata: dict = field(default_factory=dict)   # inherited from parent Document