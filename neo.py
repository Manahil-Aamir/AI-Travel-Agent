# Typical Neo4j connection setup
from neo4j import GraphDatabase

uri = "neo4j+s://41490e1b.databases.neo4j.io"  # Sometimes more reliable
driver = GraphDatabase.driver(uri, auth=("neo4j", "nquE6Nl4I6MCaKxsvgAxh_wV7L-GWffrTNb14lu1OEQ"))

# Test connection
try:
    driver.verify_connectivity()
    print("Connected to Neo4j successfully")
except Exception as e:
    print(f"Neo4j connection failed: {e}")