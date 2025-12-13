"""
Tests for Simplified Ontology v2.0

These tests validate:
1. Entity type migration (18 → 12)
2. Pydantic validation (graceful, not strict)
3. Query-time inference prompts
4. Multi-hop retrieval scenarios

Run: python -m pytest tests/test_simplified_ontology.py -v
"""

import pytest
from typing import List, Dict

# Import v2 schema
from src.ontology.schema_v2 import (
    VALID_ENTITY_TYPES_V2,
    EntityTypeV2,
    migrate_entity_type,
    create_entity,
    BaseEntityV2,
    RequirementV2,
    EvaluationFactorV2,
    WinStrategyV2,
    RelationshipV2,
    ExtractionResultV2,
    RELATIONSHIP_TYPES_V2,
)

# Config helpers inlined to avoid lightrag dependency in tests
def get_workload_analysis_prompt() -> str:
    """Query-time workload analysis prompt."""
    return """
When the user asks about workload, staffing, or basis of estimate (BOE):

1. **Extract from requirement descriptions**: Look for volumes, frequencies, shifts, quantities
   - "500 calls per day" → Labor driver
   - "24/7 operations" → Shift coverage
   - "100 receptacles emptied daily" → Workload volume
   
2. **Categorize into BOE categories**:
   - Labor: FTEs, roles, shifts, coverage
   - Materials: Equipment, supplies, consumables
   - ODCs: Travel, licenses, subcontracts
   - QA: Inspections, audits, quality control
   - Logistics: Transportation, delivery
   - Lifecycle: Maintenance, sustainment
   - Compliance: Certifications, documentation

3. **Preserve specificity**: Include the exact numbers from requirements

4. **Link to requirements**: Cite which requirements drive each workload element
"""


def get_shipley_methodology_prompt() -> str:
    """Shipley methodology prompt for capture queries."""
    return """
For Shipley Associates capture methodology queries:

**Pursuit Decision Phase**:
- Identify opportunity fit and probability of win (Pwin)
- Extract customer hot buttons from RFP emphasis language

**Capture Planning Phase**:
- Identify discriminators: What sets us apart?
- Proof points: What evidence validates claims?
- Win themes: Overarching positioning messages

**Proposal Development Phase**:
- Pink Team: Compliance check, outline review
- Red Team: Persuasiveness, win themes visible
- Gold Team: Final quality review

**Risk Identification**:
- Capture risks: Can we compete effectively?
- Execution risks: Can we perform if awarded?
"""


def get_entity_type_definitions() -> str:
    """Concise entity type definitions."""
    return """
Entity Types in this knowledge graph:

- **requirement**: Contractual obligations (shall/must statements)
- **deliverable**: CDRLs, reports, work products
- **evaluation_factor**: Section M scoring criteria
- **compliance_item**: Section L format/submission instructions
- **win_strategy**: Themes, discriminators, proof points
- **risk**: Capture and execution risks
- **section**: RFP sections (A-M, SOW/PWS)
- **document**: Attachments, standards, references
- **regulation**: FAR/DFARS/agency clauses
- **organization**: Agencies, contractors
- **program**: Contract/program names
- **reference**: Miscellaneous important references
"""


class TestEntityTypeCount:
    """Verify 12 core entity types."""
    
    def test_entity_type_count(self):
        """Should have exactly 12 entity types."""
        assert len(VALID_ENTITY_TYPES_V2) == 12
    
    def test_required_types_present(self):
        """Core types must be present."""
        required = {
            "requirement", "deliverable", "evaluation_factor",
            "compliance_item", "win_strategy", "risk",
            "section", "document", "regulation",
            "organization", "program", "reference"
        }
        assert required == VALID_ENTITY_TYPES_V2
    
    def test_removed_types_not_present(self):
        """Old types should be removed."""
        removed = {"concept", "event", "technology", "person", "location", "equipment"}
        for old_type in removed:
            assert old_type not in VALID_ENTITY_TYPES_V2


class TestEntityTypeMigration:
    """Test migration from 18-type to 12-type ontology."""
    
    def test_direct_mapping(self):
        """Types that map directly."""
        assert migrate_entity_type("requirement") == "requirement"
        assert migrate_entity_type("deliverable") == "deliverable"
        assert migrate_entity_type("evaluation_factor") == "evaluation_factor"
    
    def test_consolidated_mapping(self):
        """Types that merge into others."""
        assert migrate_entity_type("performance_metric") == "requirement"
        assert migrate_entity_type("clause") == "regulation"
        assert migrate_entity_type("submission_instruction") == "compliance_item"
        assert migrate_entity_type("strategic_theme") == "win_strategy"
        assert migrate_entity_type("statement_of_work") == "section"
    
    def test_removed_mapping(self):
        """Removed types should map to closest match."""
        assert migrate_entity_type("concept") == "reference"
        assert migrate_entity_type("event") == "reference"
        assert migrate_entity_type("technology") == "reference"
        assert migrate_entity_type("person") == "organization"
        assert migrate_entity_type("location") == "organization"
        assert migrate_entity_type("equipment") == "requirement"
    
    def test_case_insensitive(self):
        """Migration should be case-insensitive."""
        assert migrate_entity_type("REQUIREMENT") == "requirement"
        assert migrate_entity_type("Clause") == "regulation"
        assert migrate_entity_type("CONCEPT") == "reference"
    
    def test_unknown_type_fallback(self):
        """Unknown types should gracefully fallback."""
        assert migrate_entity_type("random_type") == "reference"
        assert migrate_entity_type("invented") == "reference"


class TestGracefulValidation:
    """Test that validation is graceful, not strict."""
    
    def test_minimal_entity_creation(self):
        """Entity creation with only required fields."""
        entity = BaseEntityV2(
            entity_name="Test Entity",
            entity_type="requirement"
        )
        assert entity.entity_name == "Test Entity"
        assert entity.entity_type == "requirement"
        assert entity.description == ""  # Optional, default empty
    
    def test_requirement_without_workload(self):
        """Requirement should not require workload fields."""
        req = RequirementV2(
            entity_name="24/7 Support Requirement",
            entity_type="requirement",
            description="Contractor shall provide 24/7 support with 500 calls/day"
        )
        # Should succeed without labor_drivers, material_needs
        assert req.entity_name == "24/7 Support Requirement"
        assert req.criticality == ""  # Optional
        assert req.modal_verb == ""  # Optional
    
    def test_evaluation_factor_without_subfactors(self):
        """EvaluationFactor should not require subfactors."""
        factor = EvaluationFactorV2(
            entity_name="Factor 1: Technical Approach",
            entity_type="evaluation_factor",
            description="Most Important (45%)"
        )
        # Should succeed without subfactors list
        assert factor.entity_name == "Factor 1: Technical Approach"
        assert factor.weight == ""  # Optional
    
    def test_entity_type_coercion(self):
        """Invalid entity types should coerce, not fail."""
        entity = BaseEntityV2(
            entity_name="Old Type Entity",
            entity_type="concept"  # Old type, should coerce to 'reference'
        )
        assert entity.entity_type == "reference"  # Coerced
    
    def test_name_cleanup(self):
        """Entity names should be cleaned of LLM artifacts."""
        entity = BaseEntityV2(
            entity_name="### **Bold Entity Name**",
            entity_type="requirement"
        )
        assert entity.entity_name == "Bold Entity Name"  # Cleaned


class TestCreateEntityFactory:
    """Test the create_entity factory function."""
    
    def test_creates_correct_subclass(self):
        """Factory should create correct entity subclass."""
        req = create_entity("requirement", "Test Req", "Description")
        assert isinstance(req, RequirementV2)
        
        factor = create_entity("evaluation_factor", "Factor 1", "Description")
        assert isinstance(factor, EvaluationFactorV2)
        
        strategy = create_entity("win_strategy", "Theme 1", "Description")
        assert isinstance(strategy, WinStrategyV2)
    
    def test_migrates_old_types(self):
        """Factory should migrate old types."""
        # Old 'performance_metric' → new 'requirement'
        entity = create_entity("performance_metric", "99.9% Uptime", "Metric")
        assert entity.entity_type == "requirement"
        assert isinstance(entity, RequirementV2)
        
        # Old 'clause' → new 'regulation'
        entity = create_entity("clause", "FAR 52.212-4", "Clause text")
        assert entity.entity_type == "regulation"


class TestRelationships:
    """Test relationship model."""
    
    def test_relationship_creation(self):
        """Basic relationship creation."""
        rel = RelationshipV2(
            source_entity="Requirement A",
            target_entity="Factor 1",
            relationship_type="EVALUATED_BY"
        )
        assert rel.source_entity == "Requirement A"
        assert rel.confidence == 0.7  # Default
    
    def test_focused_relationship_types(self):
        """Should have 7 focused relationship types."""
        assert len(RELATIONSHIP_TYPES_V2) == 7
        assert "HAS_REQUIREMENT" in RELATIONSHIP_TYPES_V2
        assert "EVALUATED_BY" in RELATIONSHIP_TYPES_V2
        assert "PRODUCES" in RELATIONSHIP_TYPES_V2


class TestExtractionResult:
    """Test extraction result container."""
    
    def test_empty_result(self):
        """Empty result should be valid."""
        result = ExtractionResultV2()
        assert len(result.entities) == 0
        assert len(result.relationships) == 0
    
    def test_with_entities(self):
        """Result with entities."""
        result = ExtractionResultV2(
            entities=[
                BaseEntityV2(entity_name="Entity 1", entity_type="requirement"),
                BaseEntityV2(entity_name="Entity 2", entity_type="deliverable"),
            ]
        )
        assert len(result.entities) == 2


class TestQueryPrompts:
    """Test query-time inference prompts."""
    
    def test_workload_prompt_content(self):
        """Workload prompt should have BOE categories."""
        prompt = get_workload_analysis_prompt()
        assert "Labor" in prompt
        assert "Materials" in prompt
        assert "BOE" in prompt
        assert "500 calls per day" in prompt  # Example
    
    def test_shipley_prompt_content(self):
        """Shipley prompt should have methodology phases."""
        prompt = get_shipley_methodology_prompt()
        assert "Pursuit Decision" in prompt
        assert "Capture Planning" in prompt
        assert "Pink Team" in prompt
        assert "Red Team" in prompt
        assert "discriminator" in prompt.lower()
    
    def test_entity_definitions_concise(self):
        """Entity definitions should be concise."""
        defs = get_entity_type_definitions()
        # Should be under 2000 chars (concise)
        assert len(defs) < 2000
        # Should have all 12 types
        for entity_type in VALID_ENTITY_TYPES_V2:
            assert entity_type in defs


class TestEvaluationQueries:
    """
    Test queries that should improve with simplified ontology.
    
    These are the queries mentioned in the task that should surface
    granular details after simplification.
    """
    
    @pytest.mark.parametrize("query,expected_types", [
        (
            "What workload volumes and frequencies from this RFP's requirements drive the proposed solution?",
            ["requirement"]  # Workload in requirement descriptions, not separate entities
        ),
        (
            "What are the win themes and discriminators for this opportunity?",
            ["win_strategy"]  # Consolidated from strategic_theme
        ),
        (
            "List all Section L requirements that map to Section M evaluation factors",
            ["compliance_item", "evaluation_factor"]  # L→M mapping
        ),
        (
            "What CDRLs are required and what requirements do they satisfy?",
            ["deliverable", "requirement"]
        ),
        (
            "What are the specific staffing requirements for 24/7 operations?",
            ["requirement"]  # Staffing in requirement descriptions
        ),
    ])
    def test_query_entity_types(self, query: str, expected_types: List[str]):
        """
        Verify that expected entity types exist for evaluation queries.
        
        This is a structural test - actual retrieval tested separately.
        """
        for entity_type in expected_types:
            assert entity_type in VALID_ENTITY_TYPES_V2, f"Expected type '{entity_type}' for query: {query}"


class TestWorkloadInDescription:
    """
    Test that workload details are preserved in descriptions.
    
    Key improvement: Workload should be in requirement description,
    NOT extracted into separate entities.
    """
    
    def test_workload_in_description(self):
        """Workload details should be in description field."""
        # Create requirement the v2 way - workload in description
        req = RequirementV2(
            entity_name="Help Desk Support Requirement",
            entity_type="requirement",
            description=(
                "Contractor shall provide Tier 1 and Tier 2 help desk support "
                "24 hours per day, 7 days per week. The help desk shall handle "
                "approximately 500 calls per day with average handle time of 8 minutes."
            )
        )
        
        # Workload details preserved in description
        assert "500 calls per day" in req.description
        assert "24 hours per day" in req.description
        assert "8 minutes" in req.description
        
        # NO separate labor_drivers field required
        # This enables query-time analysis with full context


class TestShipleyAlignment:
    """Test Shipley Associates methodology alignment."""
    
    def test_win_strategy_type_exists(self):
        """win_strategy type should exist for Shipley themes."""
        assert "win_strategy" in VALID_ENTITY_TYPES_V2
    
    def test_risk_type_exists(self):
        """risk type should exist for capture/execution risks."""
        assert "risk" in VALID_ENTITY_TYPES_V2
    
    def test_compliance_item_for_section_l(self):
        """compliance_item should handle Section L instructions."""
        item = create_entity(
            "compliance_item",
            "Technical Volume Format",
            "25 pages maximum, 12pt Times New Roman"
        )
        assert item.entity_type == "compliance_item"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
