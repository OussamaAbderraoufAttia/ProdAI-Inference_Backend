from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LogisticsInsight:
    insight_id: str
    timestamp: str
    category: str
    observation: str
    confidence: float
    impact: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

    @classmethod
    def create(cls, category: str, observation: str, confidence: float, 
               impact: Dict[str, Any], recommendations: List[Dict[str, Any]]):
        return cls(
            insight_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            category=category,
            observation=observation,
            confidence=confidence,
            impact=impact,
            recommendations=recommendations
        )

@dataclass
class LogisticsPlan:
    plan_id: str
    timestamp: str
    action: str
    details: Dict[str, Any]

    @classmethod
    def create(cls, action: str, details: Dict[str, Any]):
        return cls(
            plan_id=str(uuid4()),
            timestamp=datetime.now().isoformat(),
            action=action,
            details=details
        )

class LogisticsAgent:
    def __init__(self):
        self.insights: List[LogisticsInsight] = []
        self.plans: List[LogisticsPlan] = []

    def analyze_logistics_data(self, query: str, data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            # Placeholder for logistics analysis logic
            insights = [
                LogisticsInsight.create(
                    category="delivery_optimization",
                    observation="Optimize delivery routes to reduce costs.",
                    confidence=0.85,
                    impact={"cost_savings": 10000},
                    recommendations=[{"action": "optimize_routes", "priority": "HIGH"}]
                )
            ]
            self.insights.extend(insights)

            plans = [
                LogisticsPlan.create(
                    action="optimize_routes",
                    details={"current_routes": ["Route_A", "Route_B"], "proposed_routes": ["Route_C"]}
                )
            ]
            self.plans.extend(plans)

            return {
                "insights": [vars(insight) for insight in insights],
                "plans": [vars(plan) for plan in plans]
            }
        except Exception as e:
            logger.error(f"Error in logistics analysis: {str(e)}")
            return {"error": str(e)}

    def get_historical_insights(self, category: Optional[str] = None, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        filtered_insights = self.insights
        if category:
            filtered_insights = [i for i in filtered_insights if i.category == category]
        filtered_insights = [i for i in filtered_insights if i.confidence >= min_confidence]
        return [vars(insight) for insight in filtered_insights]