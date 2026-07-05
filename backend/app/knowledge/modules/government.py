import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.government")


class GovernmentKnowledgeProvider(KnowledgeProvider):
    """
    Catalog holding official government welfare programs, eligibility rules,
    application procedures, and document requirements.

    Each scheme includes structured eligibility_rules for the EligibilityEngine.
    """
    def __init__(self) -> None:
        self.schemes: list[dict[str, Any]] = [
            {
                "id": "pm-kisan",
                "title": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
                "authority": "Central Government",
                "department": "Department of Agriculture and Farmers Welfare",
                "benefits": "INR 6,000 per year paid in three equal installments of INR 2,000 directly to bank accounts.",
                "eligibility_criteria": ["All landholding farmer families", "Exclude institutional landowners", "Exclude income tax payers"],
                "eligibility_rules": [
                    {"field": "land_size_hectares", "operator": "gt", "value": 0, "description": "Must own cultivable land", "required": True},
                    {"field": "has_bank_account", "operator": "eq", "value": True, "description": "Must have a linked bank account", "required": True},
                    {"field": "has_aadhaar", "operator": "eq", "value": True, "description": "Must have Aadhaar card", "required": True},
                    {"field": "income_bracket", "operator": "not_in", "value": ["Above 5 Lakh", "Above 10 Lakh"], "description": "Should not be an income tax payer", "required": True},
                    {"field": "is_tenant", "operator": "eq", "value": False, "description": "Must be a landowner, not a tenant", "required": False},
                ],
                "application_process": "Apply online at pmkisan.gov.in portal or via Common Service Centers (CSC).",
                "application_steps": [
                    "Visit pmkisan.gov.in or nearest CSC center",
                    "Click on 'New Farmer Registration'",
                    "Enter Aadhaar number and state details",
                    "Fill in land records and bank account details",
                    "Submit application and note reference number",
                    "Verification by local patwari within 15 days",
                ],
                "required_documents": ["Aadhaar Card", "Landholding Records / Patta", "Bank Account Details", "Mobile Number"],
                "deadline": "Rolling application, updated quarterly.",
                "helpline": "155261 / 011-23381092",
                "nearest_office": "Common Service Center (CSC) or District Agriculture Office",
                "official_url": "https://pmkisan.gov.in",
                "expected_timeline": "2-4 weeks for verification",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium"],
                "tags": ["income support", "money", "subsidy", "financial aid", "central scheme", "pm kisan", "samman nidhi"],
            },
            {
                "id": "pmfby",
                "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "Comprehensive crop insurance cover against crop failure. Premium: 2% Kharif, 1.5% Rabi, 5% commercial crops. Government pays remaining premium.",
                "eligibility_criteria": ["All farmers including sharecroppers", "Must grow notified crops in notified areas"],
                "eligibility_rules": [
                    {"field": "active_crops", "operator": "exists", "value": None, "description": "Must have active crops to insure", "required": True},
                    {"field": "has_bank_account", "operator": "eq", "value": True, "description": "Must have bank account for premium deduction", "required": True},
                    {"field": "has_aadhaar", "operator": "eq", "value": True, "description": "Aadhaar required for enrollment", "required": True},
                ],
                "application_process": "Apply via national crop insurance portal (pmfby.gov.in) or local bank branch.",
                "application_steps": [
                    "Visit nearest bank branch or pmfby.gov.in",
                    "Fill crop insurance application form",
                    "Submit land ownership or tenancy proof",
                    "Pay applicable premium (2% Kharif / 1.5% Rabi)",
                    "Get insurance policy number",
                    "Report crop loss within 72 hours to helpline",
                ],
                "required_documents": ["Land possession certificate", "Sowing certificate", "Aadhaar Card", "Bank passbook", "Crop details"],
                "deadline": "Rabi: December 31; Kharif: July 31.",
                "helpline": "1800-200-7710 (Toll Free)",
                "nearest_office": "District Agriculture Office or Bank Branch",
                "official_url": "https://pmfby.gov.in",
                "expected_timeline": "Policy issued within 1 week, claims within 2 months",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["insurance", "crop loss", "damage", "premium", "subsidy", "safety net", "bima", "fasal"],
            },
            {
                "id": "soil-health-card",
                "title": "Soil Health Card Scheme",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "Free printed soil reports with 12 parameters (NPK, pH, EC, etc.) and corrective dosage recommendations to improve yield.",
                "eligibility_criteria": ["All farmers possessing cultivable lands"],
                "eligibility_rules": [
                    {"field": "land_size_hectares", "operator": "gt", "value": 0, "description": "Must have cultivable land for soil sampling", "required": True},
                ],
                "application_process": "Soil samples collected by local agriculture officers, cards dispatched to villages.",
                "application_steps": [
                    "Contact local agriculture extension officer",
                    "Provide land details and location",
                    "Officer collects soil sample from your field",
                    "Sample analyzed at soil testing laboratory",
                    "Soil Health Card delivered within 3-4 weeks",
                    "Follow fertilizer recommendations on card",
                ],
                "required_documents": ["Farmer name", "Aadhaar Card", "Land location details"],
                "deadline": "Samples collected bi-annually.",
                "helpline": "1800-180-1551",
                "nearest_office": "Krishi Vigyan Kendra (KVK) or Block Agriculture Office",
                "official_url": "https://soilhealth.dac.gov.in",
                "expected_timeline": "3-4 weeks for card delivery",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["soil testing", "npk", "fertilizer", "nutrition", "soil card", "soil health"],
            },
            {
                "id": "kcc",
                "title": "Kisan Credit Card (KCC)",
                "authority": "Central Government / RBI",
                "department": "All Commercial Banks and Co-operatives",
                "benefits": "Flexible short-term credit up to INR 3 lakh at 4% interest (with subvention). Covers crop cultivation, post-harvest, and allied activities.",
                "eligibility_criteria": ["Individual/Joint cultivators", "Tenant farmers", "Sharecroppers", "Self Help Groups"],
                "eligibility_rules": [
                    {"field": "has_bank_account", "operator": "eq", "value": True, "description": "Must have bank account", "required": True},
                    {"field": "has_aadhaar", "operator": "eq", "value": True, "description": "KYC via Aadhaar required", "required": True},
                    {"field": "active_crops", "operator": "exists", "value": None, "description": "Must be engaged in cultivation", "required": True},
                ],
                "application_process": "Submit KCC application form to any local public sector bank.",
                "application_steps": [
                    "Visit nearest public sector bank branch",
                    "Request KCC application form",
                    "Fill form with personal and land details",
                    "Submit identity, address, and land documents",
                    "Bank processes application within 14 days",
                    "Receive KCC with credit limit based on land holding",
                ],
                "required_documents": ["Identity proof (Aadhaar)", "Address proof", "Land records / Patta", "Sowing proof / Crop certificate", "Passport-size photograph"],
                "deadline": "No hard deadline. KCC valid for 5 years, renewable annually.",
                "helpline": "Contact nearest bank branch",
                "nearest_office": "Nearest Public Sector Bank Branch",
                "official_url": "https://www.nabard.org",
                "expected_timeline": "14 working days for approval",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["credit", "loan", "borrowing", "money", "interest subvention", "finance", "kcc", "kisan credit"],
            },
            {
                "id": "pm-kusum",
                "title": "Pradhan Mantri Kisan Urja Suraksha evam Utthaan Mahabhiyan (PM-KUSUM)",
                "authority": "Central Government",
                "department": "Ministry of New and Renewable Energy (MNRE)",
                "benefits": "60% subsidy on solar pump installation. Components: solar pumps up to 7.5 HP, grid-connected solar plants, solarization of existing pumps.",
                "eligibility_criteria": ["Farmers with agricultural land", "Water source availability (borewell, canal, etc.)"],
                "eligibility_rules": [
                    {"field": "land_size_hectares", "operator": "gte", "value": 0.5, "description": "Minimum 0.5 hectare land required", "required": True},
                    {"field": "water_source", "operator": "exists", "value": None, "description": "Must have existing water source for solar pump", "required": False},
                ],
                "application_process": "Apply through state renewable energy agency or MNRE portal.",
                "application_steps": [
                    "Register on PM-KUSUM portal or state energy agency website",
                    "Select component (solar pump / grid plant / solarization)",
                    "Submit land and water source documents",
                    "Pay farmer share (40% of cost)",
                    "Approved vendor installs solar pump",
                    "Commissioning and testing by agency",
                ],
                "required_documents": ["Land records", "Aadhaar Card", "Bank account details", "Electricity bill (for solarization)", "Water source proof"],
                "deadline": "Open until scheme targets are met.",
                "helpline": "1800-180-3333",
                "nearest_office": "State Renewable Energy Development Agency (SREDA)",
                "official_url": "https://pmkusum.mnre.gov.in",
                "expected_timeline": "4-8 weeks for installation",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["solar", "pump", "energy", "electricity", "irrigation", "kusum", "renewable"],
            },
            {
                "id": "pmkmy",
                "title": "Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)",
                "authority": "Central Government",
                "department": "Ministry of Agriculture and Farmers Welfare",
                "benefits": "INR 3,000 per month pension after age 60. Government matches farmer's monthly contribution (INR 55-200 based on age).",
                "eligibility_criteria": ["Small and marginal farmers", "Age 18-40 years", "Not covered under other pension schemes"],
                "eligibility_rules": [
                    {"field": "farmer_category", "operator": "in", "value": ["Small", "Marginal"], "description": "Only for small and marginal farmers", "required": True},
                    {"field": "has_aadhaar", "operator": "eq", "value": True, "description": "Aadhaar required for enrollment", "required": True},
                    {"field": "has_bank_account", "operator": "eq", "value": True, "description": "Bank account needed for contribution and pension", "required": True},
                    {"field": "land_size_hectares", "operator": "lte", "value": 2.0, "description": "Land holding must be 2 hectares or less", "required": True},
                ],
                "application_process": "Enroll at nearest CSC center with Aadhaar and bank details.",
                "application_steps": [
                    "Visit nearest Common Service Center (CSC)",
                    "Carry Aadhaar card and bank passbook",
                    "Select monthly contribution amount based on age",
                    "Authorize auto-debit from bank account",
                    "Receive enrollment confirmation and Kisan Pension Card",
                ],
                "required_documents": ["Aadhaar Card", "Bank passbook with IFSC", "Age proof"],
                "deadline": "Open enrollment.",
                "helpline": "1800-267-6888 (Toll Free)",
                "nearest_office": "Common Service Center (CSC)",
                "official_url": "https://maandhan.in",
                "expected_timeline": "Same-day enrollment at CSC",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal"],
                "tags": ["pension", "old age", "retirement", "social security", "maandhan"],
            },
            {
                "id": "rkvy",
                "title": "Rashtriya Krishi Vikas Yojana (RKVY-RAFTAAR)",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "Project-based grants for agri-infrastructure, innovation, and value chain development. Up to INR 25 lakh for agripreneurship.",
                "eligibility_criteria": ["Farmer groups", "FPOs", "Agripreneurs", "State agriculture departments"],
                "eligibility_rules": [
                    {"field": "land_size_hectares", "operator": "gt", "value": 0, "description": "Must be engaged in agriculture", "required": True},
                ],
                "application_process": "Apply through state agriculture department or RKVY portal.",
                "application_steps": [
                    "Identify project area (infrastructure, innovation, value chain)",
                    "Contact state agriculture department",
                    "Submit detailed project proposal",
                    "State committee reviews and approves",
                    "Funds released in installments based on milestones",
                ],
                "required_documents": ["Project proposal", "Land records", "Aadhaar Card", "FPO registration (if applicable)"],
                "deadline": "Varies by state allocation cycle.",
                "helpline": "State agriculture department helpline",
                "nearest_office": "State Agriculture Department / Directorate",
                "official_url": "https://rkvy.nic.in",
                "expected_timeline": "2-3 months for project approval",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["infrastructure", "innovation", "value chain", "agripreneurship", "rkvy"],
            },
            {
                "id": "drip-sprinkler",
                "title": "Per Drop More Crop — Micro Irrigation Subsidy",
                "authority": "Central Government",
                "department": "Ministry of Agriculture (PMKSY)",
                "benefits": "55% subsidy for small/marginal farmers and 45% for others on drip and sprinkler irrigation systems.",
                "eligibility_criteria": ["All farmers with own or leased land", "Water source available"],
                "eligibility_rules": [
                    {"field": "land_size_hectares", "operator": "gte", "value": 0.2, "description": "Minimum 0.2 hectare for micro irrigation", "required": True},
                    {"field": "water_source", "operator": "exists", "value": None, "description": "Water source required for irrigation system", "required": False},
                ],
                "application_process": "Apply through state horticulture or agriculture department.",
                "application_steps": [
                    "Visit state agriculture / horticulture department website",
                    "Register and submit application online",
                    "Upload land and water source documents",
                    "Department inspects and approves",
                    "Purchase system from empaneled vendor",
                    "Submit bills for subsidy reimbursement",
                ],
                "required_documents": ["Land records", "Aadhaar Card", "Bank details", "Water source proof", "Quotation from vendor"],
                "deadline": "Subject to annual state allocation.",
                "helpline": "State agriculture department helpline",
                "nearest_office": "District Horticulture Officer / Agriculture Office",
                "official_url": "https://pmksy.gov.in",
                "expected_timeline": "4-6 weeks for approval",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["drip", "sprinkler", "irrigation", "water", "micro irrigation", "subsidy"],
            },
            {
                "id": "nmoop",
                "title": "National Mission on Oilseeds and Oil Palm (NMOOP)",
                "authority": "Central Government",
                "department": "Department of Agriculture",
                "benefits": "Seeds subsidy, demonstration plots, and INR 29,000/ha for oil palm fresh fruit bunch purchase. Mini oil processing units subsidized.",
                "eligibility_criteria": ["Farmers growing oilseed crops", "Oil palm cultivators"],
                "eligibility_rules": [
                    {"field": "active_crops", "operator": "any", "value": ["Mustard", "Groundnut", "Soybean", "Sunflower", "Oil Palm", "Sesame"], "description": "Must grow oilseed or oil palm crops", "required": True},
                    {"field": "land_size_hectares", "operator": "gte", "value": 0.2, "description": "Minimum land for oilseed cultivation", "required": True},
                ],
                "application_process": "Apply through state agriculture department oilseed mission.",
                "application_steps": [
                    "Contact state oilseed mission office",
                    "Register as oilseed / oil palm grower",
                    "Submit crop and land details",
                    "Receive subsidized seeds and inputs",
                    "Attend demonstration plots training",
                ],
                "required_documents": ["Land records", "Aadhaar Card", "Crop cultivation proof"],
                "deadline": "Season-based enrollment.",
                "helpline": "State agriculture department helpline",
                "nearest_office": "State Oilseed Mission Office",
                "official_url": "https://nmoop.gov.in",
                "expected_timeline": "2-3 weeks for seed distribution",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium", "Large"],
                "tags": ["oilseed", "mustard", "groundnut", "soybean", "oil palm", "sunflower"],
            },
            {
                "id": "organic-farming",
                "title": "Paramparagat Krishi Vikas Yojana (PKVY) — Organic Farming",
                "authority": "Central Government",
                "department": "Ministry of Agriculture",
                "benefits": "INR 50,000/hectare over 3 years for organic farming conversion. Includes certification costs, inputs, and marketing support.",
                "eligibility_criteria": ["Farmers willing to adopt organic practices", "Cluster of 20+ farmers preferred"],
                "eligibility_rules": [
                    {"field": "is_organic", "operator": "eq", "value": True, "description": "Must practice or intend to practice organic farming", "required": False},
                    {"field": "land_size_hectares", "operator": "gte", "value": 0.4, "description": "Minimum 1 acre (0.4 ha) for organic certification", "required": True},
                ],
                "application_process": "Form a cluster of 20+ farmers and apply through regional centre of organic farming.",
                "application_steps": [
                    "Form cluster group with 20+ neighbouring farmers",
                    "Contact Regional Centre of Organic Farming (RCOF)",
                    "Submit group application with land details",
                    "Undergo organic conversion training",
                    "Follow organic protocols for 3 years",
                    "Receive PGS-India organic certification",
                ],
                "required_documents": ["Land records", "Aadhaar Card", "Cluster group agreement", "Farmer consent forms"],
                "deadline": "Rolling enrollment, cluster-based.",
                "helpline": "1800-180-1551",
                "nearest_office": "Regional Centre of Organic Farming (RCOF)",
                "official_url": "https://pgsindia-ncof.gov.in",
                "expected_timeline": "3-year conversion period",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal", "Medium"],
                "tags": ["organic", "natural farming", "chemical free", "pkvy", "certification"],
            },
            {
                "id": "mahila-kisan",
                "title": "Mahila Kisan Sashaktikaran Pariyojana (MKSP)",
                "authority": "Central Government",
                "department": "Ministry of Rural Development (under NRLM)",
                "benefits": "Capacity building, skill training, and livelihood support for women farmers. Up to INR 7,500/woman farmer for inputs and training.",
                "eligibility_criteria": ["Women farmers", "Self Help Group members"],
                "eligibility_rules": [
                    {"field": "gender", "operator": "eq", "value": "Female", "description": "Exclusively for women farmers", "required": True},
                ],
                "application_process": "Through Self Help Groups (SHGs) and state rural livelihood missions.",
                "application_steps": [
                    "Join or form a Self Help Group (SHG)",
                    "Register with state rural livelihood mission",
                    "Submit MKSP project proposal through SHG",
                    "Undergo skill training and capacity building",
                    "Receive input support and livelihood assistance",
                ],
                "required_documents": ["Aadhaar Card", "SHG membership proof", "Bank passbook"],
                "deadline": "Rolling through SHG channel.",
                "helpline": "NRLM helpline: 1800-180-5353",
                "nearest_office": "Block Level NRLM Office / DRDA",
                "official_url": "https://nrlm.gov.in",
                "expected_timeline": "1-2 months for SHG-based enrollment",
                "state_applicability": [],
                "farmer_categories": ["Small", "Marginal"],
                "gender_specific": "Female",
                "tags": ["women", "mahila", "women farmer", "SHG", "empowerment", "skill training"],
            },
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Government schemes search: '{query}'")
        query_lower = query.lower()
        results = []
        for scheme in self.schemes:
            score = 0.0
            if query_lower in scheme["title"].lower():
                score += 0.8
            if query_lower in scheme["benefits"].lower():
                score += 0.4
            if any(query_lower in tag for tag in scheme.get("tags", [])):
                score += 0.5
            for criterion in scheme.get("eligibility_criteria", []):
                if query_lower in criterion.lower():
                    score += 0.3

            # Partial word matching for broader recall
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:
                    if word in scheme["title"].lower():
                        score += 0.3
                    if word in scheme["benefits"].lower():
                        score += 0.2
                    if any(word in tag for tag in scheme.get("tags", [])):
                        score += 0.3
                    if word in scheme.get("department", "").lower():
                        score += 0.1

            if score > 0.0:
                results.append({
                    "id": scheme["id"],
                    "title": scheme["title"],
                    "content": f"{scheme['title']} provides: {scheme['benefits']}. Eligibility: {', '.join(scheme.get('eligibility_criteria', []))}.",
                    "metadata": {
                        "authority": scheme["authority"],
                        "department": scheme["department"],
                        "required_documents": scheme.get("required_documents", []),
                        "deadline": scheme.get("deadline", ""),
                        "helpline": scheme.get("helpline", ""),
                        "official_url": scheme.get("official_url", ""),
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "government_schemes_db"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    def get_all_schemes(self) -> list[dict[str, Any]]:
        """Return all schemes with full data for eligibility evaluation."""
        return self.schemes

    def get_scheme_by_id(self, scheme_id: str) -> dict[str, Any] | None:
        """Look up a scheme by its ID."""
        for scheme in self.schemes:
            if scheme["id"] == scheme_id:
                return scheme
        return None

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "GovernmentKnowledge",
            "status": "healthy",
            "schemes_count": len(self.schemes)
        }
