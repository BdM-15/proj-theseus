// =============================================================================
// Workspace: Document Hierarchy
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Shows sections, documents, attachments structure
// =============================================================================
MATCH
  (parent:dla_tire_ont1)-[r:CONTAINS|CHILD_OF|PART_OF]->(child:dla_tire_ont1)
WHERE
  parent.entity_type IN ['section', 'document', 'attachment'] OR
  child.entity_type IN ['section', 'document', 'attachment']
RETURN parent, r, child
LIMIT 100;