"""Handles Neo4j Database """
from neo4j import GraphDatabase

class Neo4jHandler:
    """Class containing handler methods"""
    def __init__(self, uri, user, password):
        """ Create a connection to the Neo4j DB"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """ Close the database connection when done"""
        self.driver.close()

    # Save website nodes (URL, name, and timestamp) into the graph
    def save_websites(self, websites):
        """
        Save website nodes (URL, title, and timestamp) into the graph.
        `websites` is a list of dicts like:
        {"title": "...", "url": "...", "timestamp": "..."}
        """
        with self.driver.session() as session:
            for w in websites:
                session.run(
                    """
                    MERGE (s:Website {url: $url})
                    SET s.title = $title, s.timestamp = $timestamp
                    """,
                    url=w["url"], title=w["title"], timestamp=w["timestamp"]
                )

    def save_similarities(self, similarities):
        """Save similarity relationships (scores) between websites"""
        with self.driver.session() as session:
            for w1, w2, score in similarities:
                session.run(
                    """
                    MATCH (a:Website {url: $url1})
                    MATCH (b:Website {url: $url2})
                    MERGE (a)-[r1:SIMILAR_TO]->(b)
                    SET r1.score = $score
                    MERGE (b)-[r2:SIMILAR_TO]->(a)
                    SET r2.score = $score
                    """,
                    url1=w1, url2=w2, score=float(score)
                )

    # Fetch the top_k most similar websites for a given URL
    def recommend_similar(self, url, top_k=5):
        """
        Fetch the top_k most similar websites for a given URL.
        Returns a list of (recommended_url, similarity_score).
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Website {url: $url})-[r:SIMILAR_TO]->(b:Website)
                RETURN b.url AS recommended, r.score AS similarity
                ORDER BY r.score DESC
                LIMIT $top_k
                """,
                url=url, top_k=top_k
            )
            return [(record["recommended"], record["similarity"]) for record in result]

    def exists_website(self, url):
        """Check if a Website node with the given URL already exists in the database"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (w:Website {url: $url}) RETURN w LIMIT 1",
                url=url
            )
            return result.single() is not None

    def get_all_websites(self):
        """Returns list of all websites """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (w:Website) RETURN w.url AS url, w.title AS title, w.timestamp AS timestamp"
            )
            return [dict(record) for record in result]
