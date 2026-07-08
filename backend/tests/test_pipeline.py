import pytest
from app.core.config import settings
from app.core.container import Container
from app.knowledge_pipeline.document_parser import (
    DocumentParser,
    ParsedDocument,
    ParsedSection,
)
from app.knowledge_pipeline.pipeline_manager import PipelineManager
from app.knowledge_pipeline.validation_engine import ValidationEngine
from app.knowledge_pipeline.version_manager import VersionManager


def test_document_parser_formats() -> None:
    parser = DocumentParser()

    # 1. Test Markdown Parsing
    md_content = """# Crop Nutrition
## Nitrogen Split
Apply nitrogen in three split doses for wheat.
| Crop | Dose |
| Wheat | 120kg/ha |
"""
    doc_md = parser.parse_document(md_content, "md", "md-001")
    assert doc_md.title == "Crop Nutrition"
    assert len(doc_md.sections) == 1
    assert doc_md.sections[0].heading == "Nitrogen Split"
    assert len(doc_md.sections[0].tables) == 1
    assert doc_md.sections[0].tables[0][0] == ["Crop", "Dose"]

    # 2. Test JSON Parsing
    json_content = """{
        "title": "Irrigation Guide",
        "version": "1.2.0",
        "language": "hi",
        "sections": [
            {"heading": "Watering", "content": "Water wheat every 15 days."}
        ]
    }"""
    doc_json = parser.parse_document(json_content, "json", "json-002")
    assert doc_json.title == "Irrigation Guide"
    assert doc_json.version == "1.2.0"
    assert doc_json.language == "hi"
    assert doc_json.sections[0].heading == "Watering"

    # 3. Test CSV Parsing
    csv_content = "Wheat,120,Punjab\nRice,150,Haryana"
    doc_csv = parser.parse_document(csv_content, "csv", "csv-003")
    assert len(doc_csv.sections) == 1
    assert len(doc_csv.sections[0].tables[0]) == 2
    assert doc_csv.sections[0].tables[0][0] == ["Wheat", "120", "Punjab"]

    # 4. Test Simulated PDF Parsing
    pdf_content = "[title] PM-Kisan Circular\n[version] 2.1.0\n[language] en\nThis circular outlines details about cash transfer benefit payouts."
    doc_pdf = parser.parse_document(pdf_content, "pdf", "pdf-004")
    assert doc_pdf.title == "PM-Kisan Circular"
    assert doc_pdf.version == "2.1.0"
    assert doc_pdf.language == "en"
    assert "cash transfer" in doc_pdf.sections[0].content

def test_validation_engine_rules() -> None:
    version_mgr = VersionManager()
    val_engine = ValidationEngine(version_mgr)

    # 1. Valid Document Ingestion
    doc = ParsedDocument(
        doc_id="doc-001",
        title="Weed Control Manual",
        sections=[ParsedSection(heading="Herbicides", content="Spray isoproturon.")],
        version="1.0.0"
    )
    report = val_engine.validate_document(doc)
    assert report.valid is True
    assert report.hash_checksum is not None

    # 2. Duplicate Detection
    report_dup = val_engine.validate_document(doc)
    assert report_dup.valid is True  # Same ID, matches previous hash
    assert any("matches previously indexed version" in w for w in report_dup.warnings)

    # Duplicate content with different ID
    doc_dup_diff_id = ParsedDocument(
        doc_id="doc-002",
        title="Weed Control Manual",
        sections=[ParsedSection(heading="Herbicides", content="Spray isoproturon.")],
        version="1.0.0"
    )
    report_dup_diff_id = val_engine.validate_document(doc_dup_diff_id)
    assert report_dup_diff_id.valid is False
    assert any("Duplicate document content detected" in e for e in report_dup_diff_id.errors)

    # 3. Missing Fields
    broken_doc = ParsedDocument(doc_id="", title="", sections=[], version="")
    report_broken = val_engine.validate_document(broken_doc)
    assert report_broken.valid is False
    assert len(report_broken.errors) >= 3

def test_version_manager_rollbacks_and_diffs() -> None:
    mgr = VersionManager()

    doc_v1 = ParsedDocument(
        doc_id="doc-001",
        title="Sowing Advisory",
        sections=[ParsedSection(heading="Date", content="Sow in November.")],
        version="1.0.0"
    )
    doc_v2 = ParsedDocument(
        doc_id="doc-001",
        title="Sowing Advisory",
        sections=[ParsedSection(heading="Date", content="Sow in mid-November.")],
        version="1.1.0"
    )

    mgr.register_version(doc_v1, "hash1", status="published")
    assert mgr.get_active_published("doc-001").version == "1.0.0"

    mgr.register_version(doc_v2, "hash2", status="published")
    assert mgr.get_active_published("doc-001").version == "1.1.0"
    assert mgr.history["doc-001"][1].status == "archived"  # V1 should be archived

    # Test Rollback
    mgr.rollback_to_version("doc-001", "1.0.0")
    assert mgr.get_active_published("doc-001").version == "1.0.0"
    assert mgr.history["doc-001"][0].status == "archived"  # V2 is now archived

    # Test Diff
    diff = mgr.generate_diff("doc-001", "1.0.0", "1.1.0")
    assert "+Sow in mid-November." in diff
    assert "-Sow in November." in diff

@pytest.mark.asyncio
async def test_end_to_end_knowledge_ingestion_workflow() -> None:
    # 1. Instantiate the PipelineManager in standalone DI Container context
    container = Container(settings)
    pm = PipelineManager(container)

    # Ingest document
    json_data = """{
        "title": "Soil Organic Matter",
        "version": "1.0.0",
        "sections": [
            {"heading": "Organic Content", "content": "Maintain high carbon levels in soil."}
        ],
        "metadata": {"source": "Soil Institute", "tags": ["soil", "organic"]}
    }"""

    res = await pm.ingest_document(json_data, "json", "soil-doc-99")

    assert res["status"] == "success"
    assert res["doc_id"] == "soil-doc-99"
    assert res["version"] == "1.0.0"
    assert res["checksum"] != ""

    # 2. Check if published and searchable in the vector stores (FAISS and Chroma)
    registry = container.knowledge_platform.manager.registry

    # Query FAISS vector provider
    faiss_prov = registry.get("faiss")
    faiss_results = await faiss_prov.similarity_search("carbon soil")
    assert len(faiss_results) > 0
    assert "carbon levels" in faiss_results[0]["content"]

    # Query Chroma vector provider
    chroma_prov = registry.get("chroma")
    chroma_results = await chroma_prov.similarity_search("carbon soil")
    assert len(chroma_results) > 0
    assert "carbon levels" in chroma_results[0]["content"]

    # 3. Check Observability metrics
    obs = container.observability_manager
    metrics = obs.metrics()
    assert "ingestion_time" in metrics
    assert "embedding_latency" in metrics
    assert "version_count" in metrics
    assert metrics["version_count"]["latest"] == 1.0
