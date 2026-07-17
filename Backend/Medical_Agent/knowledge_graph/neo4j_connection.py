import os
from neo4j import GraphDatabase, exceptions
from dotenv import load_dotenv

load_dotenv()


class Neo4jConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
            cls._instance._driver = None
        return cls._instance

    def connect(self):
        if self._driver is None:
            uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            user = os.getenv('NEO4J_USER', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', 'password')
            try:
                self._driver = GraphDatabase.driver(uri, auth=(user, password))
                with self._driver.session() as session:
                    session.run("RETURN 1")
                print("Neo4j connection successful")
            except exceptions.Neo4jError as e:
                print(f"Neo4j connection error: {e}")
                raise

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def query(self, cypher, params=None):
        if self._driver is None:
            self.connect()
        try:
            with self._driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except exceptions.Neo4jError as e:
            print(f"Neo4j query error: {e}")
            raise

    def is_connected(self):
        if self._driver is None:
            return False
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            return False


neo4j_conn = Neo4jConnection()
