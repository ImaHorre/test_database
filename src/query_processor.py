"""
Natural Language Query Processor

Parses natural language queries and routes them to appropriate DataAnalyst methods.
Uses pattern matching and keyword detection for intent classification.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    """Represents the parsed intent of a natural language query."""
    intent_type: str  # compare, filter, analyze, track, plot, report, help, list
    entities: Dict[str, any]  # Extracted parameters
    confidence: float  # 0.0 to 1.0
    raw_query: str  # Original query


class QueryProcessor:
    """
    Processes natural language queries and extracts structured intent.

    Supported intents:
    - compare: Compare devices, device types, parameters
    - filter: Filter data by criteria
    - analyze: Analyze parameter effects, correlations
    - track: Track device performance over time
    - plot: Generate visualizations
    - report: Generate summary reports
    - list: List available devices, parameters, etc.
    - help: Get help with query syntax
    """

    def __init__(self):
        """Initialize query processor with pattern matchers."""
        self.intent_patterns = self._build_intent_patterns()
        self.entity_extractors = self._build_entity_extractors()

    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for intent detection."""
        return {
            'compare': [
                r'\b(compare|comparison)\b',
                r'\b(versus|vs\.?)\b',
                r'\b(difference|differences)\b',
                r'\b(between)\b',
            ],
            'filter': [
                r'\b(filter|show me|give me|find)\b',
                r'\b(only|just|where)\b',
                r'\b(with|having|at)\b.*\b(flowrate|pressure|fluid)\b',
            ],
            'analyze': [
                r'\b(analyze|analysis|effect|impact|influence)\b',
                r'\b(correlation|relationship)\b',
                r'\b(how does|what effect)\b',
            ],
            'track': [
                r'\b(track|monitor|follow|history)\b',
                r'\b(over time|across dates|temporal)\b',
                r'\b(performance of|tracking)\b',
            ],
            'plot': [
                r'\b(plot|graph|chart|visualize|visualization)\b',
                r'\b(show.*plot|create.*graph)\b',
            ],
            'plot_dfu': [
                r'\b(across|vs|versus)\b.*\bdfu\b',
                r'\bdfu\b.*\b(rows?|numbers?)\b',
                r'\b(show|plot|display)\b.*\b(across|for|at)\b.*\b(measured|all)\b.*\bdfu',
                r'\ball\s+measured\s+dfus?\b',
            ],
            'report': [
                r'\b(report|summary|summarize)\b',
                r'\b(generate.*report|create.*summary)\b',
            ],
            'list': [
                r'\b(list|show all|what are|available)\b.*\b(devices|parameters|types)\b',
                r'\b(which devices|what devices)\b',
            ],
            'help': [
                r'\b(help|how to|what can)\b',
                r'\?$',  # Questions ending with ?
            ],
        }

    def _build_entity_extractors(self) -> Dict[str, callable]:
        """Build entity extraction functions."""
        return {
            'device_type': self._extract_device_type,
            'device_id': self._extract_device_id,
            'flowrate': self._extract_flowrate,
            'pressure': self._extract_pressure,
            'fluid': self._extract_fluid,
            'metric': self._extract_metric,
            'dfu_row': self._extract_dfu_row,
            'date': self._extract_date,
        }

    def process_query(self, query: str) -> QueryIntent:
        """
        Process a natural language query and extract intent.

        Args:
            query: Natural language query string

        Returns:
            QueryIntent object with parsed information
        """
        query = query.strip()
        logger.info(f"Processing query: {query}")

        # Detect intent
        intent_type, confidence = self._detect_intent(query)

        # Extract entities
        entities = self._extract_entities(query)

        # Build QueryIntent
        intent = QueryIntent(
            intent_type=intent_type,
            entities=entities,
            confidence=confidence,
            raw_query=query
        )

        logger.info(f"Detected intent: {intent_type} (confidence: {confidence:.2f})")
        logger.info(f"Extracted entities: {entities}")

        return intent

    def _detect_intent(self, query: str) -> Tuple[str, float]:
        """
        Detect query intent using pattern matching.

        Returns:
            Tuple of (intent_type, confidence)
        """
        query_lower = query.lower()

        # Score each intent
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            scores[intent] = score

        # Get best matching intent
        if max(scores.values()) == 0:
            return 'help', 0.0

        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]

        # Calculate confidence (normalize by max possible score)
        confidence = min(max_score / len(self.intent_patterns[best_intent]), 1.0)

        return best_intent, confidence

    def _extract_entities(self, query: str) -> Dict[str, any]:
        """
        Extract all entities from query.

        Returns:
            Dictionary of entity_type: value
        """
        entities = {}

        for entity_type, extractor in self.entity_extractors.items():
            value = extractor(query)
            if value is not None:
                entities[entity_type] = value

        return entities

    def _extract_device_type(self, query: str) -> Optional[str]:
        """Extract device type (W13, W14, etc.)."""
        match = re.search(r'\b(W1[34])\b', query, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _extract_device_id(self, query: str) -> Optional[str]:
        """Extract device ID (W13_S1_R1, etc.)."""
        match = re.search(r'\b(W1[34]_S\d+_R\d+)\b', query, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _extract_flowrate(self, query: str) -> Optional[int]:
        """Extract flowrate in ml/hr."""
        # Look for patterns like "5 ml/hr", "5ml/hr", "5 mlhr", "flowrate of 5"
        patterns = [
            r'(\d+)\s*ml\s*/?\s*h?r?',
            r'flowrate\s+(?:of\s+)?(\d+)',
            r'(\d+)\s*flowrate',
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_pressure(self, query: str) -> Optional[int]:
        """Extract pressure in mbar."""
        # Look for patterns like "500 mbar", "500mbar", "pressure of 500"
        patterns = [
            r'(\d+)\s*mbar',
            r'pressure\s+(?:of\s+)?(\d+)',
            r'(\d+)\s*pressure',
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_fluid(self, query: str) -> Optional[str]:
        """Extract fluid type."""
        fluids = ['NaCas', 'SDS', 'SO']
        query_upper = query.upper()

        for fluid in fluids:
            if fluid in query_upper:
                return fluid
        return None

    def _extract_metric(self, query: str) -> Optional[str]:
        """Extract metric name."""
        metrics = {
            'droplet size': 'droplet_size_mean',
            'droplet': 'droplet_size_mean',
            'size': 'droplet_size_mean',
            'frequency': 'frequency_mean',
            'freq': 'frequency_mean',
        }

        query_lower = query.lower()
        for keyword, metric_name in metrics.items():
            if keyword in query_lower:
                return metric_name

        # Default to droplet size
        return None

    def _extract_dfu_row(self, query: str) -> Optional[int]:
        """Extract DFU row number."""
        match = re.search(r'DFU\s*(\d+)', query, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _extract_date(self, query: str) -> Optional[str]:
        """Extract date (basic implementation)."""
        # Look for dates in format DDMMYYYY or DD/MM/YYYY
        match = re.search(r'(\d{2})[/\-]?(\d{2})[/\-]?(\d{4})', query)
        if match:
            return f"{match.group(1)}{match.group(2)}{match.group(3)}"
        return None

    def suggest_clarification(self, intent: QueryIntent) -> Optional[str]:
        """
        Suggest clarifying questions based on missing entities.

        Args:
            intent: QueryIntent object

        Returns:
            Clarifying question string or None
        """
        if intent.intent_type == 'compare':
            if 'device_type' not in intent.entities and 'device_id' not in intent.entities:
                return "What would you like to compare? (e.g., device types W13 vs W14, or specific devices)"

        elif intent.intent_type == 'filter':
            if not intent.entities:
                return "What criteria would you like to filter by? (device type, flowrate, pressure, fluid type)"

        elif intent.intent_type == 'analyze':
            if 'device_type' not in intent.entities:
                return "Which device type would you like to analyze? (W13 or W14)"
            if 'flowrate' not in intent.entities and 'pressure' not in intent.entities:
                return "Which parameter should I analyze? (flowrate or pressure)"

        elif intent.intent_type == 'track':
            if 'device_id' not in intent.entities:
                return "Which device would you like to track? (e.g., W13_S1_R1)"

        return None


def format_query_help() -> str:
    """Generate help text for query syntax."""
    return """
Natural Language Query Help
==================================================

You can ask questions in natural language. Here are some examples:

COMPARISONS:
  - "Compare W13 and W14 devices"
  - "Compare devices at 5 ml/hr flowrate"
  - "Show me the difference between W13 and W14"
  - "Compare all devices at 500 mbar pressure"

FILTERING:
  - "Show me all W13 devices"
  - "Filter by flowrate 5 ml/hr"
  - "Find devices with NaCas fluid"
  - "Show me devices at 5 ml/hr and 500 mbar"

ANALYSIS:
  - "Analyze flowrate effects for W13"
  - "What's the effect of pressure on droplet size?"
  - "Show correlation between flowrate and droplet size"
  - "Analyze parameter effects for W14"

TRACKING:
  - "Track W13_S1_R1 over time"
  - "Show device history for W13_S1_R2"
  - "Monitor W14_S1_R1 performance"
  - "How has W13_S1_R1 performed over time?"

DFU ANALYSIS (NEW):
  - "Show droplet size across all measured DFUs for W13 at 5mlhr200mbar"
  - "Plot frequency across DFUs for each W14 device at 30mlhr300mbar"
  - "Show me the droplet size across all measured DFUs for each w13 device"
  - "Display frequency vs DFU rows for W13 devices"

PLOTTING:
  - "Plot device type comparison"
  - "Visualize flowrate effects"
  - "Create a graph of W13 vs W14"
  - "Plot DFU row performance"

REPORTING:
  - "Generate a summary report"
  - "Create a report"
  - "Summarize the data"

LISTING:
  - "List all devices"
  - "What devices are available?"
  - "Show me all device types"
  - "Which devices have been tested?"

TIPS:
  - Be specific about device types (W13, W14) when possible
  - Include flow parameters (e.g., "5 ml/hr", "500 mbar") for better filtering
  - You can combine multiple criteria (e.g., "Compare W13 devices at 5 ml/hr")
  - DFU queries create multi-line plots showing each device as a separate line
  - If the query is unclear, I'll ask clarifying questions

TYPE 'help' TO SEE THIS MESSAGE AGAIN
==================================================
"""
