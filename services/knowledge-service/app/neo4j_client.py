from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase, Driver

from app.config import get_settings


class Neo4jKG:
    """Knowledge Graph layer using Neo4j (labeled property graph + Cypher)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._driver: Driver | None = None
        self._uri = settings.neo4j_uri
        self._user = settings.neo4j_user
        self._password = settings.neo4j_password
        try:
            self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
            self._driver.verify_connectivity()
            self._ensure_constraints()
        except Exception:  # noqa: BLE001
            # Allow knowledge service to boot without Neo4j; graph ops become no-ops
            if self._driver is not None:
                self._driver.close()
            self._driver = None

    @property
    def available(self) -> bool:
        return self._driver is not None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def _ensure_constraints(self) -> None:
        if not self._driver:
            return
        with self._driver.session() as session:
            session.run(
                "CREATE CONSTRAINT entity_name IF NOT EXISTS "
                "FOR (e:Entity) REQUIRE e.name IS UNIQUE"
            )

    def upsert_entities_and_relations(
        self,
        entities: list[str],
        relations: list[tuple[str, str, str]],
        source_url: str | None = None,
    ) -> tuple[int, int]:
        if not self._driver:
            return 0, 0
        ent_count = 0
        rel_count = 0
        with self._driver.session() as session:
            for name in entities:
                session.run(
                    """
                    MERGE (e:Entity {name: $name})
                    ON CREATE SET e.created_at = datetime(), e.source_url = $source
                    ON MATCH SET e.source_url = coalesce(e.source_url, $source)
                    """,
                    name=name,
                    source=source_url,
                )
                ent_count += 1
            for src, rel, dst in relations:
                rel_type = "".join(ch if ch.isalnum() else "_" for ch in rel.upper()) or "RELATED_TO"
                session.run(
                    f"""
                    MERGE (a:Entity {{name: $src}})
                    MERGE (b:Entity {{name: $dst}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    ON CREATE SET r.source_url = $source, r.created_at = datetime()
                    """,
                    src=src,
                    dst=dst,
                    source=source_url,
                )
                rel_count += 1
        return ent_count, rel_count

    def neighbors(self, entity_name: str, limit: int = 20) -> list[dict[str, Any]]:
        if not self._driver:
            return []
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (a:Entity)
                WHERE toLower(a.name) CONTAINS toLower($name)
                MATCH (a)-[r]-(b:Entity)
                RETURN a.name AS source, type(r) AS relation, b.name AS target
                LIMIT $limit
                """,
                name=entity_name,
                limit=limit,
            )
            return [
                {
                    "type": "graph",
                    "fact": f"({rec['source']})-[:{rec['relation']}]->({rec['target']})",
                    "source": rec["source"],
                    "relation": rec["relation"],
                    "target": rec["target"],
                }
                for rec in result
            ]

    def related_pair(self, left: str, right: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self._driver:
            return []
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (a:Entity), (b:Entity)
                WHERE toLower(a.name) CONTAINS toLower($left)
                  AND toLower(b.name) CONTAINS toLower($right)
                MATCH p = shortestPath((a)-[*..4]-(b))
                RETURN [n IN nodes(p) | n.name] AS nodes,
                       [r IN relationships(p) | type(r)] AS rels
                LIMIT $limit
                """,
                left=left,
                right=right,
                limit=limit,
            )
            facts: list[dict[str, Any]] = []
            for rec in result:
                nodes = rec["nodes"] or []
                rels = rec["rels"] or []
                parts: list[str] = []
                for i, node in enumerate(nodes):
                    parts.append(str(node))
                    if i < len(rels):
                        parts.append(f"-[:{rels[i]}]-")
                facts.append({"type": "graph", "fact": "".join(parts), "nodes": nodes, "rels": rels})
            return facts

    def query_from_text(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Extract likely entity mentions (Capitalized tokens) and fetch neighbors."""
        import re

        mentions = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b", query)
        # Also try significant lowercase tokens as soft contains
        soft = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", query) if t.lower() not in {
            "what", "which", "related", "about", "with", "from", "that", "this", "have", "does"
        }]
        names = list(dict.fromkeys(mentions + soft))[:5]
        facts: list[dict[str, Any]] = []
        if len(names) >= 2:
            facts.extend(self.related_pair(names[0], names[1], limit=limit))
        for name in names:
            facts.extend(self.neighbors(name, limit=max(3, limit // max(1, len(names)))))
        # dedupe
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for f in facts:
            key = f.get("fact", "")
            if key and key not in seen:
                seen.add(key)
                unique.append(f)
        return unique[:limit]


_KG: Neo4jKG | None = None


def get_kg() -> Neo4jKG:
    global _KG
    if _KG is None:
        _KG = Neo4jKG()
    elif not _KG.available:
        # Retry once if Neo4j was not ready at first boot
        try:
            _KG.close()
        except Exception:  # noqa: BLE001
            pass
        _KG = Neo4jKG()
    return _KG
