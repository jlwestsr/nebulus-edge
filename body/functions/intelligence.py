"""
title: Nebulus Intelligence
author: Nebulus Edge
version: 2.0.0
description: Query your business data with natural language, get automated insights, and provide feedback for continuous learning
"""

import os
from typing import Optional

import requests


class Tools:
    """Open WebUI Tools for Nebulus Intelligence."""

    def __init__(self):
        """Initialize with Intelligence API URL."""
        self.intelligence_url = os.getenv(
            "INTELLIGENCE_URL", "http://host.docker.internal:8081"
        )

    def ask_data(
        self,
        question: str,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Ask a natural language question about your business data.

        Use this tool when users want to:
        - Query data: "How many vehicles sold last month?"
        - Find patterns: "What do our best sales have in common?"
        - Get recommendations: "What's our ideal inventory?"
        - Analyze metrics: "What's our average days on lot?"

        :param question: The natural language question to ask about the data
        :return: Answer with supporting data and analysis
        """
        try:
            response = requests.post(
                f"{self.intelligence_url}/query/ask",
                json={"question": question},
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()

            # Format response
            answer = result.get("answer", "No answer available")
            classification = result.get("classification", "unknown")
            confidence = result.get("confidence", 0)
            sql_used = result.get("sql_used")
            supporting_data = result.get("supporting_data")

            output = f"**Answer:**\n{answer}\n\n"
            output += f"*Query Type: {classification} | Confidence: {confidence:.0%}*"

            if sql_used:
                output += f"\n\n**SQL Used:**\n```sql\n{sql_used}\n```"

            if supporting_data and len(supporting_data) > 0:
                output += (
                    f"\n\n**Supporting Data:** {len(supporting_data)} records found"
                )

            return output

        except requests.exceptions.ConnectionError:
            return (
                "Unable to connect to Intelligence service. "
                "Please ensure the service is running on port 8081."
            )
        except requests.exceptions.Timeout:
            return "The query took too long. Please try a simpler question."
        except Exception as e:
            return f"Error querying data: {str(e)}"

    def upload_csv(
        self,
        file_path: str,
        table_name: Optional[str] = None,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Upload a CSV file for analysis.

        Use this tool when users want to upload new data for analysis.

        :param file_path: Path to the CSV file to upload
        :param table_name: Optional name for the data table
        :return: Upload result with schema information
        """
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.split("/")[-1], f, "text/csv")}
                data = {}
                if table_name:
                    data["table_name"] = table_name

                response = requests.post(
                    f"{self.intelligence_url}/data/upload",
                    files=files,
                    data=data,
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()

            return (
                f"Uploaded **{result['table_name']}**:\n"
                f"- Rows: {result['rows_imported']}\n"
                f"- Columns: {', '.join(result['columns'])}\n"
                f"- Primary Key: {result.get('primary_key', 'None detected')}\n"
                f"- Records Embedded: {result.get('records_embedded', 0)}"
            )

        except FileNotFoundError:
            return f"File not found: {file_path}"
        except Exception as e:
            return f"Error uploading file: {str(e)}"

    def list_tables(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        List all available data tables.

        Use this tool when users want to see what data is available.

        :return: List of tables with row counts
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/data/tables",
                timeout=30,
            )
            response.raise_for_status()
            tables = response.json()

            if not tables:
                return "No data tables found. Upload a CSV to get started."

            output = "**Available Tables:**\n"
            for table in tables:
                output += (
                    f"- **{table['name']}**: {table['row_count']} rows, "
                    f"{len(table['columns'])} columns\n"
                )

            return output

        except Exception as e:
            return f"Error listing tables: {str(e)}"

    def get_scoring_factors(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get the scoring factors that define a "perfect" outcome.

        Use this tool when users want to understand what criteria
        are used to evaluate quality.

        :return: List of scoring factors with weights
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/knowledge/scoring",
                timeout=30,
            )
            response.raise_for_status()
            factors = response.json()

            if not factors:
                return "No scoring factors configured."

            output = "**Scoring Factors (Perfect Sale):**\n"
            for factor in factors:
                output += (
                    f"- **{factor['name']}** (weight: {factor['weight']}): "
                    f"{factor['description']}\n"
                )

            return output

        except Exception as e:
            return f"Error getting scoring factors: {str(e)}"

    def score_records(
        self,
        table_name: str,
        limit: int = 10,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Score records in a table based on quality criteria.

        Use this tool when users want to analyze the quality of their data,
        like finding their best or worst performing records.

        :param table_name: Name of the table to score
        :param limit: Maximum number of records to return
        :return: Scored records with distribution stats
        """
        try:
            response = requests.post(
                f"{self.intelligence_url}/query/score",
                json={"table_name": table_name, "limit": limit},
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            dist = result.get("distribution", {})
            output = f"**Score Distribution for {table_name}:**\n"
            output += f"- Average Score: {dist.get('avg', 0):.1f}%\n"
            output += (
                f"- Range: {dist.get('min', 0):.1f}% - {dist.get('max', 0):.1f}%\n"
            )
            output += f"- Total Records: {dist.get('count', 0)}\n\n"

            buckets = dist.get("distribution", {})
            if buckets:
                output += "**Distribution:**\n"
                for bucket, count in buckets.items():
                    output += f"- {bucket}: {count}\n"

            return output

        except Exception as e:
            return f"Error scoring records: {str(e)}"

    # ========== INSIGHTS TOOLS ==========

    def get_insights(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get automated insights from your business data.

        Use this tool when users want to:
        - See what's happening in their data
        - Find trends, anomalies, or opportunities
        - Get a health check of their business metrics

        :return: Generated insights organized by priority
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/insights/generate",
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()

            output = "**Business Insights**\n\n"
            output += f"*{result.get('summary', 'No summary available')}*\n\n"

            insights = result.get("insights", [])
            if not insights:
                return output + "No significant insights found in current data."

            # Group by priority
            by_priority = {}
            for insight in insights:
                priority = insight.get("priority", "medium")
                if priority not in by_priority:
                    by_priority[priority] = []
                by_priority[priority].append(insight)

            # Display high/critical first
            for priority in ["critical", "high", "medium", "low"]:
                if priority in by_priority:
                    emoji = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢",
                    }.get(priority, "⚪")
                    output += f"\n### {emoji} {priority.upper()} Priority\n\n"
                    for insight in by_priority[priority]:
                        output += f"**{insight['title']}**\n"
                        output += f"{insight['description']}\n"
                        if insight.get("recommendations"):
                            output += (
                                "- "
                                + "\n- ".join(insight["recommendations"][:2])
                                + "\n"
                            )
                        output += "\n"

            return output

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Intelligence service."
        except Exception as e:
            return f"Error generating insights: {str(e)}"

    def get_alerts(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get high-priority alerts requiring immediate attention.

        Use this tool when users want to see urgent issues or
        critical items that need immediate action.

        :return: High and critical priority insights only
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/insights/high-priority",
                timeout=30,
            )
            response.raise_for_status()
            insights = response.json()

            if not insights:
                return "✅ **No high-priority alerts.** Your data looks healthy!"

            output = f"⚠️ **{len(insights)} High-Priority Alert(s)**\n\n"

            for insight in insights:
                emoji = "🔴" if insight["priority"] == "critical" else "🟠"
                output += f"{emoji} **{insight['title']}**\n"
                output += f"{insight['description']}\n"
                if insight.get("recommendations"):
                    output += "\n**Action Items:**\n"
                    for rec in insight["recommendations"][:3]:
                        output += f"- {rec}\n"
                output += "\n---\n\n"

            return output

        except Exception as e:
            return f"Error getting alerts: {str(e)}"

    # ========== FEEDBACK TOOLS ==========

    def submit_feedback(
        self,
        context: str,
        rating: int,
        comment: Optional[str] = None,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Submit feedback on a query result or recommendation.

        Use this tool when users want to rate the quality of
        an answer or recommendation they received.

        :param context: Brief description of what you're rating (e.g., "query about sales")
        :param rating: Rating from -2 (very poor) to +2 (excellent). 0 = neutral
        :param comment: Optional comment explaining the rating
        :return: Confirmation of feedback submission
        """
        try:
            # Map rating to ensure it's in valid range
            rating = max(-2, min(2, rating))

            payload = {
                "feedback_type": "query_result",
                "reference_id": context[:100],  # Use context as reference
                "rating": rating,
            }
            if comment:
                payload["comment"] = comment

            response = requests.post(
                f"{self.intelligence_url}/feedback/submit",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            # Response confirms submission, no data needed from it

            rating_labels = {
                -2: "Very Poor 👎👎",
                -1: "Poor 👎",
                0: "Neutral 😐",
                1: "Good 👍",
                2: "Excellent 👍👍",
            }

            output = "✅ **Feedback Recorded**\n\n"
            output += f"- Rating: {rating_labels.get(rating, 'Unknown')}\n"
            output += f"- Context: {context}\n"
            if comment:
                output += f"- Comment: {comment}\n"
            output += "\n*Thank you! Your feedback helps improve recommendations.*"

            return output

        except Exception as e:
            return f"Error submitting feedback: {str(e)}"

    def get_feedback_summary(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get a summary of all feedback received.

        Use this tool when users want to see overall satisfaction
        metrics and feedback trends.

        :return: Feedback statistics and satisfaction rate
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/feedback/summary",
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            total = result.get("total_count", 0)
            if total == 0:
                return "No feedback recorded yet. Use `submit_feedback` after queries to help improve the system."

            output = "**Feedback Summary**\n\n"
            output += f"- Total Feedback: {total}\n"
            output += f"- Positive: {result.get('positive_count', 0)} ✅\n"
            output += f"- Neutral: {result.get('neutral_count', 0)} 😐\n"
            output += f"- Negative: {result.get('negative_count', 0)} ❌\n"
            output += f"- Average Rating: {result.get('average_rating', 0):.2f}\n"
            output += f"- Satisfaction Rate: {result.get('satisfaction_rate', 0):.0%}\n"

            return output

        except Exception as e:
            return f"Error getting feedback summary: {str(e)}"

    # ========== REFINEMENT TOOLS ==========

    def get_improvement_suggestions(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get suggestions for improving the knowledge system.

        Use this tool when users want to see what adjustments
        could be made based on feedback patterns.

        :return: Suggested weight adjustments and rule modifications
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/knowledge/refinement/analyze",
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("weight_adjustments") and not result.get(
                "rule_modifications"
            ):
                return (
                    "**No refinements suggested.**\n\n"
                    "The system needs more feedback to identify improvement patterns. "
                    "Continue using `submit_feedback` after queries."
                )

            output = "**Knowledge Refinement Suggestions**\n\n"

            adjustments = result.get("weight_adjustments", [])
            if adjustments:
                output += "### Scoring Weight Adjustments\n\n"
                for adj in adjustments:
                    direction = (
                        "↑" if adj["suggested_weight"] > adj["current_weight"] else "↓"
                    )
                    output += (
                        f"- **{adj['factor_name']}**: {adj['current_weight']} → "
                        f"{adj['suggested_weight']} {direction}\n"
                    )
                    output += (
                        f"  *{adj['reason']}* (confidence: {adj['confidence']:.0%})\n"
                    )

            modifications = result.get("rule_modifications", [])
            if modifications:
                output += "\n### Rule Modifications\n\n"
                for mod in modifications:
                    output += f"- **{mod['rule_name']}**: {mod['modification_type']}\n"
                    output += f"  *{mod['reason']}*\n"

            output += f"\n*Analysis based on {result.get('feedback_analyzed', 0)} feedback entries.*"

            return output

        except Exception as e:
            return f"Error getting improvement suggestions: {str(e)}"

    # ========== KNOWLEDGE TOOLS ==========

    def get_business_rules(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get the business rules that guide recommendations.

        Use this tool when users want to see what rules the
        system uses to filter or flag records.

        :return: List of business rules with conditions
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/knowledge/rules",
                timeout=30,
            )
            response.raise_for_status()
            rules = response.json()

            if not rules:
                return "No business rules configured."

            output = "**Business Rules**\n\n"
            for rule in rules:
                status = "✅ Active" if rule.get("active", True) else "⏸️ Inactive"
                output += f"**{rule['name']}** ({status})\n"
                output += f"- {rule['description']}\n"
                if rule.get("condition"):
                    output += f"- Condition: `{rule['condition']}`\n"
                output += "\n"

            return output

        except Exception as e:
            return f"Error getting business rules: {str(e)}"

    def get_metrics(
        self,
        __user__: Optional[dict] = None,
    ) -> str:
        """
        Get the key metrics and their target values.

        Use this tool when users want to see what metrics
        are tracked and their health thresholds.

        :return: List of metrics with targets and thresholds
        """
        try:
            response = requests.get(
                f"{self.intelligence_url}/knowledge/metrics",
                timeout=30,
            )
            response.raise_for_status()
            metrics = response.json()

            if not metrics:
                return "No metrics configured."

            output = "**Key Metrics**\n\n"
            for metric in metrics:
                output += f"**{metric['name']}**\n"
                if metric.get("description"):
                    output += f"- {metric['description']}\n"
                output += f"- Target: {metric.get('target', 'Not set')}\n"
                if metric.get("warning"):
                    output += f"- Warning: {metric['warning']}\n"
                if metric.get("critical"):
                    output += f"- Critical: {metric['critical']}\n"
                output += "\n"

            return output

        except Exception as e:
            return f"Error getting metrics: {str(e)}"
