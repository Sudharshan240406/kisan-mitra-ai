import hashlib
import logging
import random
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kisan_mitra_ai.knowledge_engine.retriever")

def get_word_embedding(word: str, dimension: int = 384) -> List[float]:
    h = hashlib.sha256(word.encode("utf-8")).hexdigest()
    state = random.getstate()
    random.seed(int(h, 16))
    vec = [random.uniform(-1.0, 1.0) for _ in range(dimension)]
    random.setstate(state)
    norm = sum(x**2 for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

def get_deterministic_embedding(text: str, dimension: int = 384) -> List[float]:
    """
    Generates a unit-normalized deterministic embedding vector of size `dimension` from a text string.
    Uses word-level embeddings to simulate semantic similarity when terms overlap.
    """
    if not text:
        return [0.0] * dimension

    stopwords = {
        "the", "a", "an", "in", "on", "at", "for", "with", "about", "against",
        "of", "by", "to", "is", "are", "and", "or", "but", "what", "how", "where", "who", "which"
    }
    words = [
        w.strip("?,.!()-+=_@#$%^&*[]{}|\\/`~'\":;").lower()
        for w in text.split()
    ]
    words = [w for w in words if w and w not in stopwords]

    if not words:
        return get_word_embedding(text.lower(), dimension)

    sum_vec = [0.0] * dimension
    for w in words:
        w_vec = get_word_embedding(w, dimension)
        for i in range(dimension):
            sum_vec[i] += w_vec[i]

    norm = sum(x**2 for x in sum_vec) ** 0.5
    if norm > 0:
        sum_vec = [x / norm for x in sum_vec]
    return sum_vec

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calculates cosine similarity between two unit vectors.
    """
    if len(v1) != len(v2) or sum(x**2 for x in v1) == 0.0 or sum(x**2 for x in v2) == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(v1, v2, strict=True))


class SemanticRetriever:
    """
    Retrieves knowledge pieces using mock embedding vectors and cosine similarity calculations.
    """
    def __init__(self, chunk_manager: Optional[Any] = None) -> None:
        self.chunk_manager = chunk_manager
        self.documents: List[Dict[str, Any]] = []
        self._seed_default_corpus()

    def add_document(
        self,
        doc_id: str,
        title: str,
        section: str,
        content: str,
        category: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Adds or updates a document in the index.
        """
        meta = metadata or {}
        doc: Dict[str, Any] = {
            "document_id": doc_id,
            "title": title,
            "section": section,
            "content": content,
            "category": category,
            "metadata": {
                "document_quality": meta.get("document_quality", 0.8),
                "confidence": meta.get("confidence", 0.8),
                "authority": meta.get("authority", "unknown"),
                "last_updated": meta.get("last_updated", time.time()),
                "version": meta.get("version", "1.0.0"),
                "source_type": meta.get("source_type", category),
                "validity_period": meta.get("validity_period", {"start": 0.0, "end": time.time() + 365 * 24 * 3600}),
                "deprecation_date": meta.get("deprecation_date", None),
                "section": section,
                "title": title,
                "document_id": doc_id,
            }
        }
        # Compute and cache embedding
        doc_emb = self.get_embedding(content)
        doc["embedding"] = doc_emb
        self.documents.append(doc)
        logger.debug(f"Retriever: Indexed document {doc_id} under category {category}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Fetches embedding, using the chunk manager's cache if available.
        """
        if self.chunk_manager:
            cached_emb: Optional[List[float]] = self.chunk_manager.get_embedding_from_cache(text)
            if cached_emb is not None:
                return cached_emb

        emb = get_deterministic_embedding(text)
        if self.chunk_manager:
            self.chunk_manager.cache_embedding(text, emb)
        return emb

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        min_similarity: float = -1.0
    ) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search. Filters optionally by category.
        """
        query_emb = self.get_embedding(query)
        results = []

        for doc in self.documents:
            # Category filter
            if category and doc["category"] != category:
                continue

            sim = cosine_similarity(query_emb, doc["embedding"])
            if sim < min_similarity:
                continue

            # Build result dictionary
            res = doc.copy()
            # Remove embedding to keep it lightweight
            res.pop("embedding", None)
            res["score"] = round(sim, 4)
            results.append(res)

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _seed_default_corpus(self) -> None:
        """
        Seeds standard baseline crop guides, government schemes, FAQs, policies, and agriculture docs.
        """
        now = time.time()

        # 1. Government Schemes
        self.add_document(
            doc_id="pm-kisan-doc",
            title="PM-Kisan Income Support Scheme",
            section="Eligibility and Benefits",
            content="The PM-KISAN scheme provides income support of INR 6,000 per year in three equal installments to all landholding farmer families across India. Institutional landowners and income tax payers are excluded. Beneficiaries must have a valid bank account linked with Aadhaar.",
            category="government_scheme",
            metadata={
                "document_quality": 0.95,
                "confidence": 0.98,
                "authority": "Central Government",
                "last_updated": now,
                "version": "2.1.0",
                "source_type": "government_portal",
                "validity_period": {"start": now - 365 * 24 * 3600, "end": now + 5 * 365 * 24 * 3600},
                "deprecation_date": None
            }
        )
        self.add_document(
            doc_id="pmfby-doc",
            title="Pradhan Mantri Fasal Bima Yojana",
            section="Crop Insurance and Premium",
            content="PMFBY offers comprehensive crop insurance cover against failure due to natural calamities. The premium paid by farmers is capped at 2% for Kharif crops, 1.5% for Rabi crops, and 5% for commercial/horticultural crops, with the remaining premium shared by central and state governments.",
            category="government_scheme",
            metadata={
                "document_quality": 0.90,
                "confidence": 0.95,
                "authority": "Ministry of Agriculture",
                "last_updated": now,
                "version": "1.8.0",
                "source_type": "government_portal",
                "validity_period": {"start": now - 365 * 24 * 3600, "end": now + 5 * 365 * 24 * 3600},
                "deprecation_date": None
            }
        )

        # 2. FAQs
        self.add_document(
            doc_id="faq-organic",
            title="FAQ: Organic Farming Best Practices",
            section="Natural Pest Control",
            content="Q: How can I control pests in organic farming? A: Use natural pest repellents like Neem seed kernel extract (NSKE), garlic-chilli paste, and release beneficial insects like trichogramma. Chemical pesticides are strictly prohibited under organic certification guidelines.",
            category="faq",
            metadata={
                "document_quality": 0.85,
                "confidence": 0.90,
                "authority": "National Centre of Organic Farming",
                "last_updated": now - 30 * 24 * 3600,
                "version": "1.0.0",
                "source_type": "faq_portal",
                "validity_period": {"start": now - 365 * 24 * 3600, "end": now + 365 * 24 * 3600},
                "deprecation_date": None
            }
        )

        # 3. Crop Guides
        self.add_document(
            doc_id="guide-wheat",
            title="Agronomic Guide for Wheat Cultivation",
            section="Sowing and Fertilizer split",
            content="For optimal wheat yields, sow seeds during November-December at a depth of 4-5 cm using a seed rate of 100 kg/ha. Apply NPK fertilizers in a 120:60:40 ratio. Split nitrogen applications: one third at sowing, one third during first irrigation, and the rest during vegetative growth.",
            category="crop_guide",
            metadata={
                "document_quality": 0.92,
                "confidence": 0.95,
                "authority": "Indian Council of Agricultural Research",
                "last_updated": now,
                "version": "3.2.0",
                "source_type": "manual",
                "validity_period": {"start": now - 365 * 24 * 3600, "end": now + 2 * 365 * 24 * 3600},
                "deprecation_date": None
            }
        )

        # 4. Agriculture Documents
        self.add_document(
            doc_id="doc-soil-prep",
            title="Soil Preparation and Conservation Techniques",
            section="Tillage and Moisture conservation",
            content="Soil preparation involves deep summer ploughing to expose pests to sunlight, followed by harrowing to create a fine tilth. Incorporate organic manure (FYM) at 10-15 tonnes per hectare to improve water holding capacity, prevent erosion, and maintain soil biology.",
            category="agriculture_document",
            metadata={
                "document_quality": 0.88,
                "confidence": 0.90,
                "authority": "Soil Survey of India",
                "last_updated": now,
                "version": "1.1.0",
                "source_type": "manual",
                "validity_period": {"start": now - 365 * 24 * 3600, "end": now + 2 * 365 * 24 * 3600},
                "deprecation_date": None
            }
        )

        # 5. Policies
        self.add_document(
            doc_id="policy-msp",
            title="Minimum Support Price (MSP) Policy",
            section="Fair Price Assurance",
            content="The Minimum Support Price (MSP) policy guarantees a price floor for 22 mandated agricultural crops based on recommendations of the Commission for Agricultural Costs and Prices (CACP). It aims to protect farmers from sharp falls in market prices and ensure equitable returns.",
            category="policy",
            metadata={
                "document_quality": 0.95,
                "confidence": 0.97,
                "authority": "CACP, Ministry of Agriculture",
                "last_updated": now,
                "version": "2026.1",
                "source_type": "policy_brief",
                "validity_period": {"start": now - 180 * 24 * 3600, "end": now + 180 * 24 * 3600},
                "deprecation_date": None
            }
        )
