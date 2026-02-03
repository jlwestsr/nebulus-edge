"""Vector search engine using ChromaDB.

Provides semantic search over business data using embeddings.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings


@dataclass
class SimilarRecord:
    """A record found via similarity search."""

    id: str
    record: Dict[str, Any]
    distance: float
    similarity: float


@dataclass
class PatternResult:
    """Result of pattern detection across similar records."""

    common_fields: Dict[str, List[Any]]
    frequent_values: Dict[str, Dict[str, int]]
    numeric_ranges: Dict[str, Dict[str, float]]
    sample_count: int


class VectorEngine:
    """Semantic search over business data using ChromaDB."""

    def __init__(self, vector_path: Path):
        """
        Initialize the vector engine.

        Args:
            vector_path: Directory for ChromaDB persistence
        """
        self.vector_path = Path(vector_path)
        self.vector_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(self.vector_path),
            settings=Settings(anonymized_telemetry=False),
        )

    def _get_collection(self, table_name: str):
        """Get or create a collection for a table."""
        return self.client.get_or_create_collection(
            name=table_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _record_to_text(self, record: Dict[str, Any]) -> str:
        """
        Convert a record to text for embedding.

        Creates a natural language representation of the record
        that captures its semantic meaning.
        """
        parts = []
        for key, value in record.items():
            if value is not None:
                # Format key as readable label
                label = key.replace("_", " ").title()
                parts.append(f"{label}: {value}")
        return ". ".join(parts)

    def embed_records(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        id_field: str,
    ) -> int:
        """
        Convert records to embeddings and store in ChromaDB.

        Args:
            table_name: Name of the collection
            records: List of record dictionaries
            id_field: Field to use as document ID

        Returns:
            Number of records embedded
        """
        if not records:
            return 0

        collection = self._get_collection(table_name)

        # Prepare documents for embedding
        ids = []
        documents = []
        metadatas = []

        for record in records:
            # Get ID from the record
            record_id = str(record.get(id_field, hash(json.dumps(record, default=str))))
            ids.append(record_id)

            # Convert record to text for embedding
            doc_text = self._record_to_text(record)
            documents.append(doc_text)

            # Store original record as metadata (stringify values for ChromaDB)
            metadata = {}
            for k, v in record.items():
                if v is None:
                    metadata[k] = ""
                elif isinstance(v, (int, float, str, bool)):
                    metadata[k] = v
                else:
                    metadata[k] = str(v)
            metadatas.append(metadata)

        # Upsert to handle re-uploads
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(records)

    def search_similar(
        self,
        table_name: str,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SimilarRecord]:
        """
        Find records semantically similar to a query.

        Args:
            table_name: Collection to search
            query: Natural language query or example text
            n_results: Maximum results to return
            filters: Optional metadata filters (ChromaDB where clause)

        Returns:
            List of similar records with distances
        """
        collection = self._get_collection(table_name)

        # Check if collection has any data
        if collection.count() == 0:
            return []

        # Build query parameters
        query_params = {
            "query_texts": [query],
            "n_results": min(n_results, collection.count()),
        }

        if filters:
            query_params["where"] = filters

        results = collection.query(**query_params)

        # Convert to SimilarRecord objects
        similar_records = []
        if results["ids"] and results["ids"][0]:
            for i, record_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                similar_records.append(
                    SimilarRecord(
                        id=record_id,
                        record=metadata,
                        distance=distance,
                        similarity=1 - distance,  # Cosine distance to similarity
                    )
                )

        return similar_records

    def search_by_example(
        self,
        table_name: str,
        record_id: str,
        n_results: int = 10,
    ) -> List[SimilarRecord]:
        """
        Find records similar to an existing record by ID.

        Args:
            table_name: Collection to search
            record_id: ID of the example record
            n_results: Maximum results to return

        Returns:
            List of similar records (excluding the example)
        """
        collection = self._get_collection(table_name)

        # Get the example record's embedding
        try:
            result = collection.get(
                ids=[record_id], include=["embeddings", "documents"]
            )
            if not result["embeddings"] or not result["embeddings"][0]:
                return []

            embedding = result["embeddings"][0]
        except Exception:
            return []

        # Query by embedding
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results + 1,  # +1 to account for the example itself
        )

        # Convert to SimilarRecord, excluding the example
        similar_records = []
        if results["ids"] and results["ids"][0]:
            for i, rid in enumerate(results["ids"][0]):
                if rid == record_id:
                    continue  # Skip the example itself

                distance = results["distances"][0][i] if results["distances"] else 0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                similar_records.append(
                    SimilarRecord(
                        id=rid,
                        record=metadata,
                        distance=distance,
                        similarity=1 - distance,
                    )
                )

        return similar_records[:n_results]

    def find_patterns(
        self,
        table_name: str,
        positive_ids: List[str],
    ) -> PatternResult:
        """
        Analyze what records with given IDs have in common.

        Useful for questions like "what makes a good sale?"
        by providing IDs of successful sales.

        Args:
            table_name: Collection to analyze
            positive_ids: IDs of "good" example records

        Returns:
            PatternResult with common characteristics
        """
        collection = self._get_collection(table_name)

        # Get the positive examples
        try:
            result = collection.get(
                ids=positive_ids,
                include=["metadatas"],
            )
        except Exception:
            return PatternResult(
                common_fields={},
                frequent_values={},
                numeric_ranges={},
                sample_count=0,
            )

        if not result["metadatas"]:
            return PatternResult(
                common_fields={},
                frequent_values={},
                numeric_ranges={},
                sample_count=0,
            )

        records = result["metadatas"]
        sample_count = len(records)

        # Analyze patterns
        common_fields: Dict[str, List[Any]] = {}
        frequent_values: Dict[str, Dict[str, int]] = {}
        numeric_ranges: Dict[str, Dict[str, float]] = {}

        # Get all field names
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())

        for field in all_fields:
            values = [r.get(field) for r in records if r.get(field) not in (None, "")]

            if not values:
                continue

            # Store all values for this field
            common_fields[field] = values

            # Check if numeric
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            if numeric_values and len(numeric_values) == len(values):
                # All values are numeric - calculate ranges
                numeric_ranges[field] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values),
                }
            else:
                # Categorical - count frequencies
                value_counts: Dict[str, int] = {}
                for v in values:
                    str_v = str(v)
                    value_counts[str_v] = value_counts.get(str_v, 0) + 1
                frequent_values[field] = value_counts

        return PatternResult(
            common_fields=common_fields,
            frequent_values=frequent_values,
            numeric_ranges=numeric_ranges,
            sample_count=sample_count,
        )

    def delete_collection(self, table_name: str) -> bool:
        """
        Delete a collection and all its embeddings.

        Args:
            table_name: Collection to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            self.client.delete_collection(name=table_name)
            return True
        except Exception:
            return False

    def list_collections(self) -> List[str]:
        """List all collections."""
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def get_collection_info(self, table_name: str) -> Dict[str, Any]:
        """Get info about a collection."""
        try:
            collection = self._get_collection(table_name)
            return {
                "name": table_name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except Exception:
            return {"name": table_name, "count": 0, "metadata": {}}
