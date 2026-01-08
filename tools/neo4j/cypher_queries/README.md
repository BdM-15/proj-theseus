# Neo4j Visualization Queries

Individual Cypher query files for VS Code's Neo4j extension.

## Usage

1. Open any `.cypher` file in VS Code
2. Connect to your Neo4j database via the Neo4j extension
3. Run the query (Ctrl+Enter or click Run)

## Query Files

### Workspace Queries (RFP Documents)

Replace `dla_tire_ont1` with your workspace name in these files:

| File                                      | Description                           |
| ----------------------------------------- | ------------------------------------- |
| `01_workspace_full_graph.cypher`          | Complete KG visualization             |
| `02_workspace_entity_stats.cypher`        | Entity type counts                    |
| `03_workspace_relationship_stats.cypher`  | Relationship type counts              |
| `04_workspace_requirements.cypher`        | Requirements and connections          |
| `05_workspace_section_l_m_mapping.cypher` | Instruction ↔ Evaluation traceability |
| `06_workspace_document_hierarchy.cypher`  | Sections, documents, attachments      |
| `07_workspace_deliverables.cypher`        | Deliverable traceability              |
| `08_workspace_orphans.cypher`             | Entities without relationships        |
| `09_workspace_hub_analysis.cypher`        | Most connected entities               |

### GovCon Ontology Queries (Evergreen Knowledge)

**Note:** These require bootstrap! If empty, run:

```bash
python tools/bootstrap_ontology.py bootstrap <workspace_name>
```

| File                                | Description                      |
| ----------------------------------- | -------------------------------- |
| `10_govcon_ontology_full.cypher`    | All ontology entities            |
| `11_govcon_ontology_modules.cypher` | Entity counts per module         |
| `12_govcon_shipley.cypher`          | Shipley methodology              |
| `13_govcon_bd_lifecycle.cypher`     | 7-Phase BD lifecycle             |
| `14_govcon_color_teams.cypher`      | Pink/Red/Gold team reviews       |
| `15_govcon_regulations.cypher`      | FAR/DFARS knowledge              |
| `16_govcon_evaluation.cypher`       | Evaluation patterns              |
| `17_govcon_capture.cypher`          | Win themes, discriminators       |
| `18_govcon_lessons_learned.cypher`  | Proposal pitfalls/best practices |

### Combined & Utility Queries

| File                                 | Description                     |
| ------------------------------------ | ------------------------------- |
| `19_combined_rfp_to_ontology.cypher` | RFP entities linked to ontology |
| `20_list_all_workspaces.cypher`      | List all workspace labels       |
| `21_database_stats.cypher`           | Overall database statistics     |

## Finding Your Workspace Name

Run `20_list_all_workspaces.cypher` to see all available workspaces:

```cypher
CALL db.labels() YIELD label RETURN label ORDER BY label;
```

Common workspaces:

- `dla_tire_ont1` - DLA Tire procurement
- `swa_tas_3d` - SWA TAS Task Order
- `default` - Default test workspace

## Why "No Records" for Ontology Queries?

The GovCon ontology must be bootstrapped into each workspace. The bootstrap injects:

- Shipley methodology concepts
- FAR/DFARS regulations
- Evaluation patterns
- Capture intelligence concepts

**To bootstrap:**

```bash
# Bootstrap specific workspace
python tools/bootstrap_ontology.py bootstrap dla_tire_ont1

# Check bootstrap status
python tools/bootstrap_ontology.py status dla_tire_ont1
```
