import csv
import io
import json
import logging
import re
from typing import Any, Dict, List

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.knowledge_pipeline.parser")

class ParsedSection(BaseModel):
    """
    Represents a single section extract from a document.
    """
    heading: str
    content: str
    tables: List[List[List[str]]] = Field(default_factory=list)

class ParsedDocument(BaseModel):
    """
    Structured payload representing a parsed knowledge document.
    """
    doc_id: str
    title: str
    sections: List[ParsedSection]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    version: str = "1.0.0"

class DocumentParser:
    """
    Extracts text, metadata, versioning, language, and table structures across multiple file formats.
    """
    def parse_document(self, content_str: str, file_type: str, doc_id: str) -> ParsedDocument:  # noqa: PLR0911
        """
        Parses document contents based on the file type extension.
        """
        file_type = file_type.lower().strip(".")
        logger.info(f"[DocumentParser] Parsing document '{doc_id}' of type '{file_type}'")

        if file_type == "json":
            return self._parse_json(content_str, doc_id)
        elif file_type == "csv":
            return self._parse_csv(content_str, doc_id)
        elif file_type in ("md", "markdown"):
            return self._parse_markdown(content_str, doc_id)
        elif file_type == "html":
            return self._parse_html(content_str, doc_id)
        elif file_type == "pdf":
            return self._parse_binary_simulation(content_str, file_type, doc_id)
        elif file_type == "docx":
            return self._parse_binary_simulation(content_str, file_type, doc_id)
        else:
            # Fallback plain text parser
            return ParsedDocument(
                doc_id=doc_id,
                title=f"Doc {doc_id}",
                sections=[ParsedSection(heading="Introduction", content=content_str)],
                metadata={"format": "txt"}
            )

    def _parse_json(self, content_str: str, doc_id: str) -> ParsedDocument:
        data = json.loads(content_str)
        title = data.get("title", f"JSON Doc {doc_id}")
        version = data.get("version", "1.0.0")
        language = data.get("language", "en")

        sections = []
        for sec in data.get("sections", []):
            sections.append(ParsedSection(
                heading=sec.get("heading", "Section"),
                content=sec.get("content", ""),
                tables=sec.get("tables", [])
            ))

        if not sections and "content" in data:
            sections.append(ParsedSection(heading="Main Content", content=data["content"]))

        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            sections=sections,
            metadata=data.get("metadata", {}),
            language=language,
            version=version
        )

    def _parse_csv(self, content_str: str, doc_id: str) -> ParsedDocument:
        # Reads CSV rows as tables
        f = io.StringIO(content_str)
        reader = csv.reader(f)
        rows = list(reader)

        title = f"CSV Dataset {doc_id}"
        metadata = {"format": "csv", "rows_count": len(rows)}

        # Expose whole table under a single section
        sections = [ParsedSection(
            heading="Data Table",
            content=f"CSV table containing {len(rows)} entries.",
            tables=[rows]
        )]

        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            sections=sections,
            metadata=metadata
        )

    def _parse_markdown(self, content_str: str, doc_id: str) -> ParsedDocument:
        # Splits sections by Heading `#` or `##`
        lines = content_str.splitlines()
        title = f"Markdown Doc {doc_id}"
        metadata = {"format": "markdown"}

        sections: List[ParsedSection] = []
        current_heading = "Header"
        current_lines: List[str] = []

        for line in lines:
            if line.startswith("#"):
                if current_lines:
                    sections.append(ParsedSection(heading=current_heading, content="\n".join(current_lines)))
                    current_lines = []
                # Strip heading chars
                current_heading = line.lstrip("#").strip()
                if line.startswith("# "):
                    title = current_heading
            else:
                current_lines.append(line)

        if current_lines or not sections:
            sections.append(ParsedSection(heading=current_heading, content="\n".join(current_lines)))

        # Simple table detection inside Markdown (e.g. lines with |)
        for sec in sections:
            table_rows = []
            for line in sec.content.splitlines():
                if "|" in line:
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if cells and not all(c.startswith("-") for c in cells):
                        table_rows.append(cells)
            if table_rows:
                sec.tables = [table_rows]

        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            sections=sections,
            metadata=metadata
        )

    def _parse_html(self, content_str: str, doc_id: str) -> ParsedDocument:
        # Extract title if present
        title_match = re.search(r"<title>(.*?)</title>", content_str, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else f"HTML Page {doc_id}"

        # Strip simple tags
        clean_text = re.sub(r"<[^>]+>", " ", content_str)
        # Condense spacing
        clean_text = " ".join(clean_text.split())

        sections = [ParsedSection(heading="Page Content", content=clean_text)]
        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            sections=sections,
            metadata={"format": "html"}
        )

    def _parse_binary_simulation(self, content_str: str, format_type: str, doc_id: str) -> ParsedDocument:
        # Simulations for PDF or DOCX parser containing raw metadata annotations
        # Extracts title and version matching headers
        title = f"Ingested {format_type.upper()} {doc_id}"
        version = "1.0.0"

        # Read mock key-value annotations in simulated binary strings
        meta_match = re.findall(r"\[(title|version|language)\]\s*([^\[\n]+)", content_str, re.IGNORECASE)
        meta_dict = {}
        for key, val in meta_match:
            meta_dict[key.lower()] = val.strip()

        if "title" in meta_dict:
            title = meta_dict["title"]
        if "version" in meta_dict:
            version = meta_dict["version"]

        clean_content = re.sub(r"\[.*?\]", "", content_str).strip()

        sections = [ParsedSection(heading="Document Content", content=clean_content)]
        return ParsedDocument(
            doc_id=doc_id,
            title=title,
            sections=sections,
            metadata={"format": format_type, "simulated": True},
            language=meta_dict.get("language", "en"),
            version=version
        )
