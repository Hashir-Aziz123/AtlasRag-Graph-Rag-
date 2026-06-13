import os
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is missing.")

class GraphDBDriver:
    _driver: Driver = None

    @classmethod
    def get_driver(cls) -> Driver:
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return cls._driver

    @classmethod
    def close_driver(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None

# Singleton driver instance export
neo4j_driver = GraphDBDriver.get_driver()