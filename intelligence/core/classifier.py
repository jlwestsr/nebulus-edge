"""Question classification for routing to appropriate engines.

Analyzes questions to determine the best approach for answering them.
"""

import json
from dataclasses import dataclass
from enum import Enum

import httpx


class QueryType(Enum):
    """Types of queries the system can handle."""

    SQL_ONLY = "sql"  # "How many cars over 60 days?"
    SEMANTIC_ONLY = "semantic"  # "Find sales like this one"
    STRATEGIC = "strategic"  # "What's ideal inventory?"
    HYBRID = "hybrid"  # Needs multiple sources


@dataclass
class ClassificationResult:
    """Result of question classification."""

    query_type: QueryType
    reasoning: str
    needs_sql: bool
    needs_semantic: bool
    needs_knowledge: bool
    suggested_tables: list[str]
    confidence: float


class QuestionClassifier:
    """Classify questions to determine how to answer them."""

    CLASSIFICATION_PROMPT = """You are a query classifier for a business intelligence system.

Analyze this question and determine how to answer it.

Question: "{question}"

Available database tables and columns:
{schema}

Question Types:
1. SQL_ONLY - Can be answered with a database query (counts, sums, filters, joins, aggregations)
   Examples: "How many vehicles?", "Average sale price last month?", "Which cars over 60 days?"

2. SEMANTIC_ONLY - Needs similarity or pattern matching, not exact queries
   Examples: "Find sales similar to this one", "What vehicles are like the Corvette?"

3. STRATEGIC - Requires reasoning about what's "best" or "ideal" using business knowledge
   Examples: "What's our ideal inventory?", "Which salespeople should we hire more like?"

4. HYBRID - Needs data from multiple approaches combined
   Examples: "What makes our best sales successful?" (needs SQL + patterns + knowledge)

Respond with JSON only:
{{
    "query_type": "sql" | "semantic" | "strategic" | "hybrid",
    "reasoning": "Brief explanation of why this classification",
    "needs_sql": true | false,
    "needs_semantic": true | false,
    "needs_knowledge": true | false,
    "suggested_tables": ["table1", "table2"],
    "confidence": 0.0 to 1.0
}}"""

    def __init__(self, brain_url: str):
        """
        Initialize the classifier.

        Args:
            brain_url: URL of the Brain LLM service
        """
        self.brain_url = brain_url

    async def classify(
        self,
        question: str,
        schema: dict,
    ) -> ClassificationResult:
        """
        Classify a question to determine how to answer it.

        Args:
            question: The user's question
            schema: Database schema information

        Returns:
            ClassificationResult with query type and flags
        """
        # Format schema for prompt
        schema_text = self._format_schema(schema)

        # Build classification prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            question=question,
            schema=schema_text,
        )

        # Call Brain for classification
        try:
            response = await self._call_brain(prompt)
            return self._parse_response(response)
        except Exception as e:
            # Default to SQL_ONLY on error
            return ClassificationResult(
                query_type=QueryType.SQL_ONLY,
                reasoning=f"Classification failed ({e}), defaulting to SQL",
                needs_sql=True,
                needs_semantic=False,
                needs_knowledge=False,
                suggested_tables=[],
                confidence=0.5,
            )

    def _format_schema(self, schema: dict) -> str:
        """Format schema dict for the prompt."""
        if not schema:
            return "No tables available"

        lines = []
        for table_name, info in schema.items():
            columns = info.get("columns", [])
            types = info.get("types", {})

            col_strs = []
            for col in columns:
                col_type = types.get(col, "TEXT")
                col_strs.append(f"{col} ({col_type})")

            lines.append(f"- {table_name}: {', '.join(col_strs)}")

        return "\n".join(lines)

    async def _call_brain(self, prompt: str) -> str:
        """Call the Brain LLM service."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.brain_url}/v1/chat/completions",
                json={
                    "model": "default",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,  # Low temperature for consistent classification
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(self, response: str) -> ClassificationResult:
        """Parse the LLM response into a ClassificationResult."""
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            # Map query type string to enum
            type_map = {
                "sql": QueryType.SQL_ONLY,
                "semantic": QueryType.SEMANTIC_ONLY,
                "strategic": QueryType.STRATEGIC,
                "hybrid": QueryType.HYBRID,
            }

            query_type = type_map.get(
                data.get("query_type", "sql").lower(),
                QueryType.SQL_ONLY,
            )

            return ClassificationResult(
                query_type=query_type,
                reasoning=data.get("reasoning", ""),
                needs_sql=data.get("needs_sql", True),
                needs_semantic=data.get("needs_semantic", False),
                needs_knowledge=data.get("needs_knowledge", False),
                suggested_tables=data.get("suggested_tables", []),
                confidence=data.get("confidence", 0.8),
            )

        except (json.JSONDecodeError, KeyError, IndexError):
            # If parsing fails, make best guess from text
            response_lower = response.lower()

            if "strategic" in response_lower or "ideal" in response_lower:
                query_type = QueryType.STRATEGIC
                needs_knowledge = True
            elif "semantic" in response_lower or "similar" in response_lower:
                query_type = QueryType.SEMANTIC_ONLY
                needs_knowledge = False
            elif "hybrid" in response_lower:
                query_type = QueryType.HYBRID
                needs_knowledge = True
            else:
                query_type = QueryType.SQL_ONLY
                needs_knowledge = False

            return ClassificationResult(
                query_type=query_type,
                reasoning="Parsed from text response",
                needs_sql=query_type in (QueryType.SQL_ONLY, QueryType.HYBRID),
                needs_semantic=query_type
                in (QueryType.SEMANTIC_ONLY, QueryType.HYBRID),
                needs_knowledge=needs_knowledge,
                suggested_tables=[],
                confidence=0.6,
            )

    def classify_simple(self, question: str) -> ClassificationResult:
        """
        Simple rule-based classification without LLM call.

        Useful for quick classification or when Brain is unavailable.
        """
        question_lower = question.lower()

        # Strategic keywords
        strategic_keywords = [
            "ideal",
            "best",
            "optimal",
            "should we",
            "recommend",
            "strategy",
            "what makes",
            "why do",
            "perfect",
        ]

        # Semantic keywords
        semantic_keywords = [
            "similar",
            "like this",
            "find like",
            "pattern",
            "common",
        ]

        # Check for strategic
        if any(kw in question_lower for kw in strategic_keywords):
            return ClassificationResult(
                query_type=QueryType.STRATEGIC,
                reasoning="Contains strategic keywords",
                needs_sql=True,
                needs_semantic=True,
                needs_knowledge=True,
                suggested_tables=[],
                confidence=0.7,
            )

        # Check for semantic
        if any(kw in question_lower for kw in semantic_keywords):
            return ClassificationResult(
                query_type=QueryType.SEMANTIC_ONLY,
                reasoning="Contains similarity keywords",
                needs_sql=False,
                needs_semantic=True,
                needs_knowledge=False,
                suggested_tables=[],
                confidence=0.7,
            )

        # Default to SQL
        return ClassificationResult(
            query_type=QueryType.SQL_ONLY,
            reasoning="Appears to be a data query",
            needs_sql=True,
            needs_semantic=False,
            needs_knowledge=False,
            suggested_tables=[],
            confidence=0.7,
        )
