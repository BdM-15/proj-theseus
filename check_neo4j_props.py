"""Check Neo4j node properties"""
from dotenv import load_dotenv
load_dotenv()

from src.inference.neo4j_graph_io import Neo4jGraphIO

io = Neo4jGraphIO()

# Get a sample node
query = """
MATCH (n:`mcpp_drfp_2025`)
RETURN properties(n) as props
LIMIT 1
"""

with io.driver.session(database=io.database) as session:
    result = session.run(query)
    record = result.single()
    if record:
        props = record['props']
        print("Properties found on nodes:")
        for key, value in props.items():
            print(f"  - {key}: {type(value).__name__}")

io.close()
