// =============================================================================
// Workspace: Section L to M Mapping (Instruction ↔ Evaluation)
// =============================================================================
// Replace 'dla_tire_ont1' with your workspace name
// Shows traceability between instructions and evaluation criteria
// =============================================================================
MATCH (inst:dla_tire_ont1 {entity_type: 'instruction'})
OPTIONAL MATCH (inst)-[r:MAPS_TO|EVALUATED_BY]->(eval:dla_tire_ont1)
WHERE
  eval.entity_type IN [
    'evaluation_factor',
    'evaluation_subfactor',
    'evaluation_criterion'
  ]
RETURN inst, r, eval;