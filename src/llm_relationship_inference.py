"""
Phase 6.1: LLM-Powered Relationship Inference

Replaces brittle regex-based patterns with semantic understanding via Grok LLM.
Reads from GraphML (correct data source), infers relationships based on content,
and saves back to knowledge graph files.

Architecture:
1. Parse GraphML to extract entity nodes with full details
2. Batch entities by type for efficient LLM processing
3. Ask Grok to infer relationships using semantic understanding
4. Parse structured JSON responses with confidence scores
5. Save new relationships back to GraphML and kv_store

Benefits:
- Agency-agnostic: Handles ANY RFP structure, not just Navy/DOD
- Context-aware: Understands content semantics, not just naming patterns
- Self-documenting: LLM provides reasoning for each relationship
- Cost-effective: ~$0.03 per document (3 batches × ~24k tokens)
- Leverages existing 2M-context Grok infrastructure
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Import relationship patterns (optional - graceful fallback if not available)
try:
    from phase6_prompts import (
        RELATIONSHIP_INFERENCE_PATTERNS,
        SECTION_NORMALIZATION_MAPPING
    )
except ImportError:
    # Fallback if phase6_prompts not available
    logger.warning("phase6_prompts not found - using default patterns")
    RELATIONSHIP_INFERENCE_PATTERNS = {}
    SECTION_NORMALIZATION_MAPPING = {}


def parse_graphml(graphml_path: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse GraphML file to extract nodes (entities) and edges (relationships).
    
    Returns:
        Tuple of (nodes, edges) where each is a list of dicts with entity/relationship details.
    """
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    # GraphML namespace
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    nodes = []
    edges = []
    
    # Extract nodes (entities)
    for node in root.findall('.//graphml:node', ns):
        node_id = node.get('id')
        node_data = {'id': node_id}
        
        # Extract data attributes (d0=entity_name, d1=entity_type, d2=description)
        for data in node.findall('graphml:data', ns):
            key = data.get('key')
            value = data.text
            
            if key == 'd0':
                node_data['entity_name'] = value
            elif key == 'd1':
                node_data['entity_type'] = value
            elif key == 'd2':
                node_data['description'] = value
        
        nodes.append(node_data)
    
    # Extract edges (relationships)
    for edge in root.findall('.//graphml:edge', ns):
        edge_id = edge.get('id')
        source = edge.get('source')
        target = edge.get('target')
        
        edge_data = {
            'id': edge_id,
            'source': source,
            'target': target
        }
        
        # Extract edge attributes (d3=keywords, d4=weight, d5=description, d6=source_id)
        for data in edge.findall('graphml:data', ns):
            key = data.get('key')
            value = data.text
            
            if key == 'd3':
                edge_data['keywords'] = value
            elif key == 'd4':
                edge_data['weight'] = float(value) if value else 0.0
            elif key == 'd5':
                edge_data['description'] = value
            elif key == 'd6':
                edge_data['source_id'] = value
        
        edges.append(edge_data)
    
    logger.info(f"  Parsed GraphML: {len(nodes)} nodes, {len(edges)} edges")
    return nodes, edges


def group_entities_by_type(nodes: List[Dict]) -> Dict[str, List[Dict]]:
    """Group entities by type for efficient batching."""
    grouped = {}
    
    for node in nodes:
        entity_type = node.get('entity_type', 'UNKNOWN')
        if entity_type not in grouped:
            grouped[entity_type] = []
        grouped[entity_type].append(node)
    
    return grouped


def create_relationship_inference_prompt(
    source_entities: List[Dict],
    target_entities: List[Dict],
    relationship_context: str
) -> str:
    """
    Create LLM prompt for semantic relationship inference.
    
    Uses phase6_prompts.py patterns as guidance for relationship types and confidence thresholds.
    Patterns are imported at module level for optimal performance.
    """
    prompt = f"""You are analyzing a government RFP knowledge graph to infer missing relationships between entities.

{relationship_context}

SOURCE ENTITIES ({len(source_entities)}):
{json.dumps([{
    'id': e.get('id'),
    'name': e.get('entity_name'),
    'type': e.get('entity_type'),
    'description': e.get('description', '')[:200]  # Truncate long descriptions
} for e in source_entities], indent=2)}

TARGET ENTITIES ({len(target_entities)}):
{json.dumps([{
    'id': e.get('id'),
    'name': e.get('entity_name'),
    'type': e.get('entity_type'),
    'description': e.get('description', '')[:200]
} for e in target_entities], indent=2)}

TASK:
Determine which source entities have meaningful relationships with which target entities based on:

1. **Naming Conventions**: Standard government contracting patterns
   - Prefix matching (e.g., "J-12345" belongs to "Section J")
   - Attachment numbering (e.g., "Annex 17" relates to "Section J Annexes")
   - Clause numbering (e.g., "FAR 52.212-1" belongs to "Section I")

2. **Content Similarity**: Semantic overlap between descriptions
   - Shared topics, keywords, or concepts
   - Explicit references (entity IDs, section numbers in text)
   - Thematic alignment

3. **Logical Document Structure**: Standard RFP organization
   - Sections contain clauses, annexes, requirements
   - Evaluation factors reference submission instructions
   - Requirements map to evaluation criteria
   - SOW/PWS content relates to deliverables

4. **Confidence Thresholds**:
   - HIGH (>0.8): Explicit naming pattern or direct reference
   - MEDIUM (0.5-0.8): Strong semantic similarity or standard structure
   - LOW (0.3-0.5): Weak semantic overlap or tentative connection

OUTPUT FORMAT:
Return a JSON array of relationship objects. Each relationship must have:
- source_id: ID of source entity
- target_id: ID of target entity
- relationship_type: One of [CHILD_OF, GUIDES, EVALUATED_BY, REFERENCES, CONTAINS, RELATED_TO]
- confidence: Float 0.0-1.0 indicating relationship strength
- reasoning: Brief explanation (1-2 sentences) of why this relationship exists

**IMPORTANT**: Only output relationships with confidence >= 0.3. Omit weak or uncertain connections.

Example output:
[
  {{
    "source_id": "node_123",
    "target_id": "node_456",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Annex J-0200000-18 has 'J-' prefix matching Section J naming pattern."
  }},
  {{
    "source_id": "node_789",
    "target_id": "node_456",
    "relationship_type": "GUIDES",
    "confidence": 0.72,
    "reasoning": "Submission instruction explicitly mentions 'Volume 1' which is referenced in evaluation factor description."
  }}
]

OUTPUT ONLY THE JSON ARRAY, NO OTHER TEXT:"""
    
    return prompt


async def infer_relationships_batch(
    source_entities: List[Dict],
    target_entities: List[Dict],
    relationship_context: str,
    llm_func
) -> List[Dict]:
    """
    Call Grok LLM to infer relationships between two groups of entities.
    
    Args:
        source_entities: List of source entity dicts
        target_entities: List of target entity dicts
        relationship_context: Context about what kind of relationships to infer
        llm_func: Async LLM function (Grok)
    
    Returns:
        List of relationship dicts with source_id, target_id, type, confidence, reasoning
    """
    prompt = create_relationship_inference_prompt(
        source_entities,
        target_entities,
        relationship_context
    )
    
    try:
        # Call Grok LLM
        response = await llm_func(
            prompt,
            system_prompt="You are a government contracting expert analyzing RFP documents. Output ONLY valid JSON.",
        )
        
        # Parse JSON response
        # Remove markdown code blocks if present
        response_clean = response.strip()
        if response_clean.startswith('```'):
            # Extract JSON from code block
            lines = response_clean.split('\n')
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or not line.startswith('```'):
                    json_lines.append(line)
            response_clean = '\n'.join(json_lines)
        
        relationships = json.loads(response_clean)
        
        if not isinstance(relationships, list):
            logger.warning(f"LLM returned non-list response: {type(relationships)}")
            return []
        
        # Validate relationship structure
        valid_relationships = []
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            
            required_fields = ['source_id', 'target_id', 'relationship_type', 'confidence', 'reasoning']
            if all(field in rel for field in required_fields):
                # Filter by confidence threshold
                if rel['confidence'] >= 0.3:
                    valid_relationships.append(rel)
        
        logger.info(f"    LLM inferred {len(valid_relationships)} relationships (filtered from {len(relationships)} raw)")
        return valid_relationships
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.error(f"Raw response: {response[:500]}")
        return []
    except Exception as e:
        logger.error(f"Error during LLM relationship inference: {e}")
        return []


async def infer_all_relationships(
    nodes: List[Dict],
    existing_edges: List[Dict],
    llm_func
) -> List[Dict]:
    """
    Infer all missing relationships using LLM semantic understanding.
    
    Strategy:
    1. Group entities by type
    2. Create batches for common relationship patterns:
       - ANNEX → SECTION (annexes to parent sections)
       - CLAUSE → SECTION (clauses to parent sections)
       - SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR (L↔M mapping)
       - REQUIREMENT → EVALUATION_FACTOR (requirements to evaluation)
       - STATEMENT_OF_WORK → DELIVERABLE (work to deliverables)
       - REQUIREMENT_THEME → REQUIREMENT (universal thematic clustering: facilities, security, technical, management, performance)
       - METHODOLOGY → EVALUATION_FACTOR (approaches supporting evaluation)
       - ANNEX → EVALUATION_FACTOR (technical annexes addressing factors)
    3. Call LLM for each batch
    4. Aggregate results
    
    Returns:
        List of new relationship dicts
    """
    logger.info("=" * 80)
    logger.info("🤖 Phase 6.1: LLM-Powered Relationship Inference")
    logger.info("=" * 80)
    
    # Group entities by type
    grouped = group_entities_by_type(nodes)
    
    logger.info(f"  Entity type distribution:")
    for entity_type, entities in sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f"    {entity_type}: {len(entities)}")
    
    # Track all inferred relationships
    all_new_relationships = []
    
    # Create set of existing relationships for deduplication
    existing_pairs = set()
    for edge in existing_edges:
        source = edge.get('source')
        target = edge.get('target')
        if source and target:
            existing_pairs.add((source, target))
            existing_pairs.add((target, source))  # Bidirectional
    
    logger.info(f"  Existing relationships: {len(existing_pairs) // 2}")
    
    # Batch 1: ANNEX → SECTION
    if 'annex' in grouped and 'section' in grouped:
        logger.info(f"\n  [Batch 1/8] Inferring ANNEX → SECTION relationships...")
        logger.info(f"    Source: {len(grouped['annex'])} annexes")
        logger.info(f"    Target: {len(grouped['section'])} sections")
        
        annex_section_rels = await infer_relationships_batch(
            source_entities=grouped['annex'],
            target_entities=grouped['section'],
            relationship_context="""
RELATIONSHIP TYPE: ANNEX → SECTION (CHILD_OF)
CONTEXT: Annexes are numbered attachments that belong to parent sections.
PATTERNS:
- Prefix matching: "J-12345" → "Section J"
- Explicit naming: "Annex 17 Transportation" → "Section J Annexes"
- Attachment numbering: "Attachment J-001" → "Section J"
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(annex_section_rels)
    
    # Batch 2: CLAUSE → SECTION
    if 'clause' in grouped and 'section' in grouped:
        logger.info(f"\n  [Batch 2/8] Inferring CLAUSE → SECTION relationships...")
        logger.info(f"    Source: {len(grouped['clause'])} clauses")
        logger.info(f"    Target: {len(grouped['section'])} sections")
        
        clause_section_rels = await infer_relationships_batch(
            source_entities=grouped['clause'],
            target_entities=grouped['section'],
            relationship_context="""
RELATIONSHIP TYPE: CLAUSE → SECTION (CHILD_OF)
CONTEXT: Contract clauses belong to parent sections (typically Section I).
PATTERNS:
- FAR/DFARS/AFFARS numbering: "FAR 52.212-1" → "Section I"
- Clause references in text: "Section K describes..." → "Section K"
- Standard contract structure: Most clauses → Section I
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(clause_section_rels)
    
    # Batch 3: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR
    if 'submission_instruction' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [Batch 3/8] Inferring SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR relationships...")
        logger.info(f"    Source: {len(grouped['submission_instruction'])} instructions")
        logger.info(f"    Target: {len(grouped['evaluation_factor'])} factors")
        
        instruction_factor_rels = await infer_relationships_batch(
            source_entities=grouped['submission_instruction'],
            target_entities=grouped['evaluation_factor'],
            relationship_context="""
RELATIONSHIP TYPE: SUBMISSION_INSTRUCTION → EVALUATION_FACTOR (GUIDES)
CONTEXT: Submission instructions (Section L) guide how proposals are evaluated (Section M).
PATTERNS:
- Explicit references: "Volume 1" mentioned in both instruction and factor
- Format requirements: Page limits, font sizes → corresponding evaluation criteria
- Semantic overlap: Instructions about "technical approach" → "Technical evaluation factor"
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(instruction_factor_rels)
    
    # Batch 4: REQUIREMENT → EVALUATION_FACTOR
    if 'requirement' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [Batch 4/8] Inferring REQUIREMENT → EVALUATION_FACTOR relationships...")
        logger.info(f"    Source: {len(grouped['requirement'])} requirements")
        logger.info(f"    Target: {len(grouped['evaluation_factor'])} factors")
        
        requirement_factor_rels = await infer_relationships_batch(
            source_entities=grouped['requirement'],
            target_entities=grouped['evaluation_factor'],
            relationship_context="""
RELATIONSHIP TYPE: REQUIREMENT → EVALUATION_FACTOR (EVALUATED_BY)
CONTEXT: Requirements are evaluated using specific evaluation factors.
PATTERNS:
- Topic alignment: "Security requirement" → "Security evaluation factor"
- Explicit mapping: Requirement IDs mentioned in evaluation criteria
- Semantic similarity: Shared technical concepts or keywords
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(requirement_factor_rels)
    
    # Batch 5: STATEMENT_OF_WORK → DELIVERABLE (includes SOW, PWS, SOO)
    if 'statement_of_work' in grouped and 'deliverable' in grouped:
        logger.info(f"\n  [Batch 5/8] Inferring STATEMENT_OF_WORK → DELIVERABLE relationships...")
        logger.info(f"    Source: {len(grouped['statement_of_work'])} work statements (SOW/PWS/SOO)")
        logger.info(f"    Target: {len(grouped['deliverable'])} deliverables")
        
        sow_deliverable_rels = await infer_relationships_batch(
            source_entities=grouped['statement_of_work'],
            target_entities=grouped['deliverable'],
            relationship_context="""
RELATIONSHIP TYPE: STATEMENT_OF_WORK → DELIVERABLE (PRODUCES)
CONTEXT: Work statements define tasks/objectives that produce specific deliverables.
SEMANTIC EQUIVALENCE: "STATEMENT_OF_WORK" entity type includes:
  - SOW (Statement of Work): Prescriptive instructions on HOW to perform work
  - PWS (Performance Work Statement): Performance-based WHAT outcomes, offeror decides HOW
  - SOO (Statement of Objectives): High-level OBJECTIVES, offeror creates PWS from SOO

All three formats describe contractor work scope and deliverables, just at different levels:
  - SOW: Detailed tasks → Specific deliverables
  - PWS: Performance standards → Outcome-based deliverables  
  - SOO: Objectives → Offeror-proposed deliverables

PATTERNS:
- Explicit mentions: "Task 1" → "Deliverable 1.1"
- Work-product mapping: "Software development task" → "Software deliverable"
- Timeline alignment: Work phases → corresponding deliverables
- Performance standards: "Maintain uptime 99.9%" → "Uptime reports"
- Objectives: "Provide secure infrastructure" → "Security certification"
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(sow_deliverable_rels)
    
    # Batch 6: REQUIREMENT_THEME → REQUIREMENT (CATEGORIZES)
    # Universal thematic clustering pattern - works for ALL RFP domains
    # Pattern: Parent theme/umbrella groups related child requirements
    if 'requirement' in grouped:
        logger.info(f"\n  [Batch 6/8] Inferring REQUIREMENT_THEME → REQUIREMENT relationships...")
        logger.info(f"    Detecting thematic clusters across all domains (facilities, security, technical, management)...")
        logger.info(f"    Analyzing {len(grouped['requirement'])} requirements for parent-child patterns")
        
        theme_rels = await infer_relationships_batch(
            source_entities=grouped['requirement'],
            target_entities=grouped['requirement'],  # Self-referential for theme detection
            relationship_context="""
RELATIONSHIP TYPE: REQUIREMENT_THEME → REQUIREMENT (CATEGORIZES)

CONTEXT: Requirements cluster under thematic categories/umbrellas regardless of RFP domain.
This is a UNIVERSAL pattern that works across all contract types (facilities, software, services, civilian).

DOMAIN-AGNOSTIC EXAMPLES:

1. FACILITIES DOMAIN (when applicable):
   - Parent: "MCSF-BI" (Marine Corps Support Facility)
   - Children: "MCSF-BI Lighting Systems", "MCSF-BI HVAC", "MCSF-BI Roofing", "MCSF-BI Cathodic Protection"
   - Pattern: Facility name appears in child requirement names or descriptions

2. SECURITY DOMAIN (universal):
   - Parent: "Security Requirements" or "Cybersecurity" or "Information Assurance"
   - Children: "NIST SP 800-171 Compliance", "FedRAMP Moderate Authorization", "Personnel Clearances", "STIG Implementation"
   - Pattern: Security-related standards, controls, certifications, clearances

3. TECHNICAL DOMAIN (universal):
   - Parent: "Technical Approach" or "Technical Integration" or "System Architecture"
   - Children: "API Gateway Requirements", "Cloud Platform Requirements", "Interface Specifications", "Systems Approach"
   - Pattern: Technical methodologies, specifications, integration points, infrastructure

4. MANAGEMENT DOMAIN (universal):
   - Parent: "Management Requirements" or "Project Management" or "Quality Assurance"
   - Children: "Monthly Status Reports", "Staffing Plan Requirements", "Quality Management System", "Risk Management Plan"
   - Pattern: Governance processes, reporting, oversight, organizational requirements

5. PERFORMANCE DOMAIN (universal):
   - Parent: "Performance Standards" or "SLA Requirements" or "Service Levels"
   - Children: "99.9% Uptime Requirement", "Response Time < 24 hours", "Throughput Standards", "Availability Metrics"
   - Pattern: Measurable outcomes, KPIs, performance metrics, service levels

6. COMPLIANCE DOMAIN (universal):
   - Parent: "Regulatory Compliance" or "Legal Requirements"
   - Children: "FAR Compliance", "Section 508 Accessibility", "HIPAA Requirements", "Environmental Regulations"
   - Pattern: Laws, regulations, standards, compliance frameworks

DETECTION LOGIC:

**Parent Theme Identification:**
- High-level requirement mentioned frequently across document (evaluation factor, facility name, domain category)
- Acts as umbrella/category for multiple related requirements
- Often appears in evaluation factors, section headers, or as organizational grouping
- May be named explicitly ("Security Requirements") or implicitly (facility name like "MCSF-BI")

**Child Requirement Identification:**
- Specific, granular requirements that fall under a theme
- Semantic overlap: Shared keywords, domain concepts, technical terms with parent
- Naming convention: Theme name/keyword appears in child entity name
- Content similarity: Child description addresses aspect of parent theme
- Hierarchical references: Child explicitly mentions parent or parent's domain

PATTERN MATCHING STRATEGIES:
1. **Naming Convention**: "MCSF-BI Lighting Systems" contains "MCSF-BI" → Parent is "MCSF-BI"
2. **Domain Alignment**: "NIST 800-171 Compliance" (security standard) → Parent is "Security Requirements"
3. **Keyword Matching**: "API Gateway Implementation" contains "API" → Parent is "Technical Integration Requirements"
4. **Semantic Similarity**: "Monthly Status Report" (management activity) → Parent is "Management Requirements"
5. **Evaluation Factor Clustering**: Requirements that support same evaluation factor may share parent theme

CONFIDENCE SCORING:
- HIGH (>0.8): Parent name explicitly in child name, direct semantic match
- MEDIUM (0.5-0.8): Strong keyword overlap, clear domain alignment, frequent co-occurrence
- LOW (0.3-0.5): Weak semantic similarity, tentative thematic connection

OUTPUT: Create CATEGORIZES relationships between parent requirement themes and child requirements.
This enables hierarchical organization in knowledge graph regardless of RFP domain (facilities, software, services, civilian).

**CRITICAL**: Look for BOTH explicit parent themes (evaluation factors, facility names) AND implicit themes 
(semantic groupings of requirements around security, technical, management, performance topics).
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(theme_rels)
    
    # Batch 7: METHODOLOGY/APPROACH → EVALUATION_FACTOR (SUPPORTS)
    # Pattern: "Systems Approach" → "Technical Approach"
    methodology_entities = [e for e in nodes if any(method in e.get('entity_name', '') 
                                                     for method in ['Approach', 'Methodology', 'Strategy', 
                                                                   'Framework', 'Process', 'Program', 'Plan'])]
    
    if 'evaluation_factor' in grouped and methodology_entities:
        logger.info(f"\n  [Batch 7/8] Inferring METHODOLOGY → EVALUATION_FACTOR relationships...")
        logger.info(f"    Source: {len(methodology_entities)} methodologies/approaches")
        logger.info(f"    Target: {len(grouped['evaluation_factor'])} evaluation factors")
        
        methodology_factor_rels = await infer_relationships_batch(
            source_entities=methodology_entities,
            target_entities=grouped['evaluation_factor'],
            relationship_context="""
RELATIONSHIP TYPE: METHODOLOGY → EVALUATION_FACTOR (SUPPORTS)
CONTEXT: Methodologies, approaches, and management systems support evaluation factors.
PATTERNS:
- Name alignment: "Systems Approach" → "Technical Approach" (shared keyword)
- Capability demonstration: "Preventative Maintenance Programs" → "Technical Approach"
- Best practices: "Best Industry Practices" → "Technical Approach"
- Management systems: "Quality Management System" → "Management Approach"
- Safety frameworks: "Safety Management System" → "Safety" factor
EXAMPLES:
- "Preventative Maintenance Programs" → "Technical Approach"
- "Systems Approach" → "Technical Approach"
- "Quality Management System" → "Management Approach"
- "Safety Management System (SMS)" → "Factor 5 - Safety"
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(methodology_factor_rels)
    
    # Batch 8: ANNEX → EVALUATION_FACTOR (ADDRESSES)
    # Pattern: "Annex 16 Utilities" → "Technical Approach"
    if 'annex' in grouped and 'evaluation_factor' in grouped:
        logger.info(f"\n  [Batch 8/8] Inferring ANNEX → EVALUATION_FACTOR relationships...")
        logger.info(f"    Source: {len(grouped['annex'])} annexes")
        logger.info(f"    Target: {len(grouped['evaluation_factor'])} evaluation factors")
        
        annex_factor_rels = await infer_relationships_batch(
            source_entities=grouped['annex'],
            target_entities=grouped['evaluation_factor'],
            relationship_context="""
RELATIONSHIP TYPE: ANNEX → EVALUATION_FACTOR (ADDRESSES)
CONTEXT: Annexes provide technical details that address specific evaluation factors.
PATTERNS:
- Technical content: "Annex 16 Utilities" → "Technical Approach"
- Domain alignment: "Annex 17 Transportation" → "Technical Approach"
- Support documentation: "Annex 15 Facilities Support" → "Technical Approach"
- Past performance: "JM-1 Corporate Experience" → "Factor 1 - Corporate Experience"
EXAMPLES:
- "Annex 16 Utilities" → "Technical Approach" (technical infrastructure details)
- "Annex 17 Transportation" → "Technical Approach" (fleet management)
- "Annex 18 Environmental" → "Technical Approach" (environmental compliance)
- "JM-4 Past Performance Questionnaire" → "Factor 6 - Past Performance"
""",
            llm_func=llm_func
        )
        all_new_relationships.extend(annex_factor_rels)
    
    # Filter out duplicates with existing relationships
    new_relationships_filtered = []
    for rel in all_new_relationships:
        source_id = rel['source_id']
        target_id = rel['target_id']
        
        if (source_id, target_id) not in existing_pairs:
            new_relationships_filtered.append(rel)
            existing_pairs.add((source_id, target_id))
            existing_pairs.add((target_id, source_id))
    
    logger.info(f"\n  ✅ LLM inference complete:")
    logger.info(f"    Total inferred: {len(all_new_relationships)}")
    logger.info(f"    After deduplication: {len(new_relationships_filtered)}")
    logger.info(f"    Filtered (duplicates): {len(all_new_relationships) - len(new_relationships_filtered)}")
    logger.info("=" * 80)
    
    return new_relationships_filtered


def save_relationships_to_graphml(
    graphml_path: Path,
    new_relationships: List[Dict],
    nodes: List[Dict]
) -> None:
    """
    Save new relationships back to GraphML file.
    
    Appends new edge elements to existing GraphML structure.
    """
    # Parse existing GraphML
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    # Find graph element
    graph = root.find('.//graphml:graph', ns)
    if graph is None:
        logger.error("Could not find graph element in GraphML")
        return
    
    # Create node ID lookup
    node_lookup = {node['id']: node for node in nodes}
    
    # Get next edge ID
    existing_edges = graph.findall('.//graphml:edge', ns)
    max_edge_id = 0
    for edge in existing_edges:
        edge_id = edge.get('id', 'e0')
        if edge_id.startswith('e'):
            try:
                edge_num = int(edge_id[1:])
                max_edge_id = max(max_edge_id, edge_num)
            except ValueError:
                pass
    
    next_edge_id = max_edge_id + 1
    
    # Add new edges
    for rel in new_relationships:
        source_id = rel['source_id']
        target_id = rel['target_id']
        rel_type = rel['relationship_type']
        confidence = rel['confidence']
        reasoning = rel['reasoning']
        
        # Create edge element
        edge = ET.SubElement(graph, 'edge')
        edge.set('id', f'e{next_edge_id}')
        edge.set('source', source_id)
        edge.set('target', target_id)
        
        # Add edge data (d3=keywords, d4=weight, d5=description, d6=source_id)
        keywords_data = ET.SubElement(edge, 'data')
        keywords_data.set('key', 'd3')
        keywords_data.text = rel_type
        
        weight_data = ET.SubElement(edge, 'data')
        weight_data.set('key', 'd4')
        weight_data.text = str(confidence)
        
        description_data = ET.SubElement(edge, 'data')
        description_data.set('key', 'd5')
        description_data.text = f"{reasoning} (LLM-inferred)"
        
        source_data = ET.SubElement(edge, 'data')
        source_data.set('key', 'd6')
        source_data.text = 'phase6.1_llm_inference'
        
        next_edge_id += 1
    
    # Write back to file
    tree.write(graphml_path, encoding='utf-8', xml_declaration=True)
    logger.info(f"  💾 Saved {len(new_relationships)} new relationships to GraphML")


def save_relationships_to_kv_store(
    rag_storage_path: Path,
    new_relationships: List[Dict],
    nodes: List[Dict]
) -> None:
    """
    Save new relationships to kv_store_full_relations.json.
    
    Appends to both individual relationship records AND document's relation_pairs array.
    """
    relations_path = rag_storage_path / "kv_store_full_relations.json"
    
    # Load existing relationships
    with open(relations_path, 'r', encoding='utf-8') as f:
        relations_data = json.load(f)
    
    # Find document key
    doc_keys = [k for k in relations_data.keys() if k.startswith('doc-')]
    if not doc_keys:
        logger.error("No document key found in kv_store_full_relations.json")
        return
    
    doc_id = doc_keys[0]
    
    # Get next relationship ID
    max_id = 0
    for rel_id in relations_data.keys():
        if rel_id.startswith('rel_'):
            try:
                id_num = int(rel_id.split('_')[1])
                max_id = max(max_id, id_num)
            except (ValueError, IndexError):
                pass
    
    next_id = max_id + 1
    
    # Create node name lookup for relation_pairs
    node_lookup = {node['id']: node.get('entity_name', 'Unknown') for node in nodes}
    
    # Add new relationships
    for rel in new_relationships:
        rel_id = f"rel_llm_{next_id}"
        relations_data[rel_id] = {
            'src_id': rel['source_id'],
            'tgt_id': rel['target_id'],
            'relationship_type': rel['relationship_type'],
            'description': f"{rel['reasoning']} (LLM-inferred, confidence={rel['confidence']:.2f})",
            'weight': rel['confidence'],
            'keywords': rel['relationship_type'],
            'source_id': 'phase6.1_llm_inference'
        }
        
        # CRITICAL: Also add to document's relation_pairs array
        src_name = node_lookup.get(rel['source_id'], 'Unknown')
        tgt_name = node_lookup.get(rel['target_id'], 'Unknown')
        relations_data[doc_id]['relation_pairs'].append([src_name, tgt_name])
        
        next_id += 1
    
    # Write back to file
    with open(relations_path, 'w', encoding='utf-8') as f:
        json.dump(relations_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  💾 Saved {len(new_relationships)} new relationships to kv_store (individual records + relation_pairs)")
