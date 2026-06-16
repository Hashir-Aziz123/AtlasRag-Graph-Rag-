import asyncio
import os
from dotenv import load_dotenv

from src.core.graph import neo4j_driver

load_dotenv()

async def dump_graph_to_text():
    """
    Connects to Neo4j, retrieves all nodes and edges, 
    and writes them to a formatted text file.
    """
    output_file = "graph_dump.txt"
    print(f"[*] Connecting to Neo4j to dump database...")

    async with neo4j_driver.session() as session:
        # Get all Nodes
        nodes_query = "MATCH (n) RETURN labels(n)[0] AS Label, n.name AS Name, n.description AS Description"
        nodes_result = await session.run(nodes_query)
        nodes = await nodes_result.data()

        # Get all Edges (Relationships)
        edges_query = "MATCH (source)-[r]->(target) RETURN source.name AS Source, type(r) AS Relationship, target.name AS Target, r.description AS Description"
        edges_result = await session.run(edges_query)
        edges = await edges_result.data()

    print(f"[*] Found {len(nodes)} Nodes and {len(edges)} Relationships.")
    print(f"[*] Writing to {output_file}...")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=========================================\n")
        f.write("GRAPH DATABASE DUMP\n")
        f.write("=========================================\n\n")

        f.write("--- NODES (ENTITIES) ---\n")
        for idx, node in enumerate(nodes, 1):
            f.write(f"{idx}. [{node['Label']}] {node['Name']}\n")
            f.write(f"    Description: {node['Description']}\n\n")

        f.write("--- EDGES (RELATIONSHIPS) ---\n")
        for idx, edge in enumerate(edges, 1):
            f.write(f"{idx}. ({edge['Source']}) -[{edge['Relationship']}]-> ({edge['Target']})\n")
            f.write(f"    Context: {edge['Description']}\n\n")

    print(f"[✔] Graph dump complete. Open '{output_file}' to view your data.")

if __name__ == "__main__":
    # Ensure the script runs using the asyncio event loop
    asyncio.run(dump_graph_to_text())