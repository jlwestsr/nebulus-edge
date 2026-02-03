"""Intelligence Orchestrator - coordinates all engines to answer questions.

The main entry point for all questions to the intelligence system.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from intelligence.core.classifier import (
    ClassificationResult,
    QueryType,
    QuestionClassifier,
)
from intelligence.core.knowledge import KnowledgeManager
from intelligence.core.sql_engine import SQLEngine
from intelligence.core.vector_engine import VectorEngine


@dataclass
class IntelligenceResponse:
    """Complete response from the intelligence system."""

    answer: str
    supporting_data: Optional[List[Dict[str, Any]]] = None
    reasoning: str = ""
    sql_used: Optional[str] = None
    similar_records: Optional[List[Dict[str, Any]]] = None
    classification: Optional[str] = None
    confidence: float = 0.0


class IntelligenceOrchestrator:
    """Main query orchestrator - coordinates all intelligence engines."""

    SYNTHESIS_PROMPT = """You are an AI business analyst. Based on the context below,
answer the user's question clearly and actionably.

Question: "{question}"

{context}

Guidelines:
- Be specific and data-driven
- Provide actionable recommendations when appropriate
- Reference the supporting data in your answer
- If the data is insufficient, say so clearly

Answer:"""

    STRATEGIC_PROMPT = """You are an AI business strategist for a {vertical}.

Question: "{question}"

{domain_knowledge}

{data_context}

Based on the domain knowledge and data above, provide strategic recommendations.
Be specific, actionable, and reference both the business rules and the actual data.

Strategic Analysis:"""

    def __init__(
        self,
        db_path: Path,
        vector_path: Path,
        knowledge_path: Path,
        brain_url: str,
        template_config: Optional[dict] = None,
        template_name: str = "generic",
    ):
        """
        Initialize the orchestrator with all required components.

        Args:
            db_path: Path to SQLite database
            vector_path: Path to vector storage
            knowledge_path: Path to knowledge JSON
            brain_url: URL of Brain LLM service
            template_config: Vertical template configuration
            template_name: Name of the vertical template
        """
        self.brain_url = brain_url
        self.template_name = template_name

        # Initialize engines
        self.sql_engine = SQLEngine(db_path, brain_url)
        self.vector_engine = VectorEngine(vector_path)
        self.knowledge = KnowledgeManager(knowledge_path, template_config)
        self.classifier = QuestionClassifier(brain_url)

    async def ask(
        self,
        question: str,
        use_simple_classification: bool = False,
    ) -> IntelligenceResponse:
        """
        Answer any question about the data.

        This is the main entry point that:
        1. Classifies the question type
        2. Gathers context from appropriate engines
        3. Injects domain knowledge if needed
        4. Synthesizes a final answer

        Args:
            question: The user's question
            use_simple_classification: Use rule-based classification (faster)

        Returns:
            IntelligenceResponse with answer and supporting data
        """
        # Get database schema for classification
        schema = self.sql_engine.get_schema()

        # Classify the question
        if use_simple_classification:
            classification = self.classifier.classify_simple(question)
        else:
            classification = await self.classifier.classify(question, schema)

        # Gather context based on classification
        context = await self._gather_context(question, classification, schema)

        # Synthesize final answer
        response = await self._synthesize(question, context, classification)

        return response

    async def _gather_context(
        self,
        question: str,
        classification: ClassificationResult,
        schema: dict,
    ) -> Dict[str, Any]:
        """Gather relevant context from appropriate engines."""
        # Extract table names from schema (schema is {"tables": {...}})
        table_names = list(schema.get("tables", {}).keys())

        context: Dict[str, Any] = {
            "sql_results": None,
            "sql_query": None,
            "similar_records": None,
            "knowledge": None,
            "tables": table_names,
        }

        # Gather SQL data if needed
        if classification.needs_sql:
            try:
                sql = await self.sql_engine.natural_to_sql(question)
                result = self.sql_engine.execute(sql)
                context["sql_query"] = sql
                context["sql_results"] = [
                    dict(zip(result.columns, row)) for row in result.rows[:50]
                ]
            except Exception as e:
                context["sql_error"] = str(e)

        # Gather semantic matches if needed
        if classification.needs_semantic:
            try:
                # Get available vector collections
                collections = self.vector_engine.list_collections()
                tables_with_vectors = [t for t in table_names if t in collections]

                # Prioritize tables mentioned in the question
                question_lower = question.lower()
                prioritized_tables = []
                other_tables = []

                for table in tables_with_vectors:
                    # Check if table name (or singular form) appears in question
                    table_singular = table.rstrip("s")  # Simple singular form
                    if table in question_lower or table_singular in question_lower:
                        prioritized_tables.append(table)
                    else:
                        other_tables.append(table)

                # Search prioritized tables first, then others
                search_order = prioritized_tables + other_tables

                for table in search_order:
                    similar = self.vector_engine.search_similar(
                        table_name=table,
                        query=question,
                        n_results=10,
                    )
                    if similar:
                        context["similar_records"] = [
                            {"table": table, "id": r.id, "record": r.record}
                            for r in similar
                        ]
                        break
            except Exception as e:
                context["semantic_error"] = str(e)

        # Inject domain knowledge if needed
        if classification.needs_knowledge:
            context["knowledge"] = self.knowledge.export_for_prompt()

        return context

    async def _synthesize(
        self,
        question: str,
        context: Dict[str, Any],
        classification: ClassificationResult,
    ) -> IntelligenceResponse:
        """Synthesize final answer from gathered context."""
        # Build context string for prompt
        context_parts = []

        if context.get("sql_results"):
            data_preview = context["sql_results"][:10]
            context_parts.append(f"## Data Results\n```json\n{data_preview}\n```")

            if context.get("sql_query"):
                context_parts.append(f"SQL Used: `{context['sql_query']}`")

        if context.get("similar_records"):
            context_parts.append(
                f"## Similar Records Found\n{context['similar_records'][:5]}"
            )

        if context.get("knowledge"):
            context_parts.append(f"## Domain Knowledge\n{context['knowledge']}")

        if context.get("sql_error"):
            context_parts.append(f"Note: SQL query failed - {context['sql_error']}")

        context_text = "\n\n".join(context_parts) if context_parts else "No data found."

        # Choose prompt based on query type
        if classification.query_type == QueryType.STRATEGIC:
            prompt = self.STRATEGIC_PROMPT.format(
                vertical=self.template_name,
                question=question,
                domain_knowledge=context.get("knowledge", "No domain knowledge."),
                data_context=context_text,
            )
        else:
            prompt = self.SYNTHESIS_PROMPT.format(
                question=question,
                context=context_text,
            )

        # Call Brain for final synthesis
        try:
            answer = await self._call_brain(prompt)
        except Exception as e:
            answer = f"I was unable to fully analyze your question: {e}"

        # Build response
        return IntelligenceResponse(
            answer=answer,
            supporting_data=context.get("sql_results"),
            reasoning=classification.reasoning,
            sql_used=context.get("sql_query"),
            similar_records=context.get("similar_records"),
            classification=classification.query_type.value,
            confidence=classification.confidence,
        )

    async def _call_brain(self, prompt: str) -> str:
        """Call the Brain LLM service for synthesis."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.brain_url}/v1/chat/completions",
                json={
                    "model": "default",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def ask_with_scoring(
        self,
        question: str,
        table_name: str,
        score_category: str = "perfect_sale",
    ) -> IntelligenceResponse:
        """
        Answer a question with scoring context.

        Automatically includes top/bottom scored records in context.
        """
        from intelligence.core.scoring import SaleScorer

        # Get scores
        scorer = SaleScorer(
            self.sql_engine.db_path,
            self.knowledge,
            category=score_category,
        )

        try:
            scored = scorer.score_table(table_name, limit=20)
            distribution = scorer.get_score_distribution(table_name)
            factor_perf = scorer.get_factor_performance(table_name)
        except Exception:
            scored = []
            distribution = {}
            factor_perf = {}

        # Build enhanced context
        score_context = f"""
## Score Distribution
{distribution}

## Factor Performance (what criteria are being met/missed)
{factor_perf}

## Top Scored Records
{[{"score": s.percentage, "record": s.record} for s in scored[:5]]}

## Lowest Scored Records
{[{"score": s.percentage, "record": s.record} for s in scored[-5:]]}
"""

        # Now run regular ask with this extra context
        response = await self.ask(question)

        # Enhance the answer with scoring context
        enhanced_prompt = f"""Based on this scoring analysis:

{score_context}

And this previous analysis:
{response.answer}

Provide enhanced recommendations considering the scoring data.
What patterns distinguish high-scoring from low-scoring records?
"""

        try:
            enhanced_answer = await self._call_brain(enhanced_prompt)
            response.answer = enhanced_answer
        except Exception:
            pass  # Keep original answer

        return response
