"""Intelligence core modules."""

from intelligence.core.ingest import DataIngestor, IngestResult
from intelligence.core.knowledge import (
    BusinessRule,
    DomainKnowledge,
    KnowledgeManager,
    Metric,
    ScoringFactor,
)
from intelligence.core.scoring import SaleScorer, ScoredRecord
from intelligence.core.sql_engine import QueryResult, SQLEngine, UnsafeQueryError
from intelligence.core.vector_engine import PatternResult, SimilarRecord, VectorEngine

__all__ = [
    "DataIngestor",
    "IngestResult",
    "SQLEngine",
    "QueryResult",
    "UnsafeQueryError",
    "KnowledgeManager",
    "DomainKnowledge",
    "ScoringFactor",
    "BusinessRule",
    "Metric",
    "SaleScorer",
    "ScoredRecord",
    "VectorEngine",
    "SimilarRecord",
    "PatternResult",
]
