"""
title: Nebulus Intelligence
author: Nebulus Edge
version: 1.0.0
description: Query your business data with natural language using Nebulus Intelligence
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
