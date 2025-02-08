from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from enum import Enum
import json
from datetime import datetime
from groq import Groq
import logging
from uuid import uuid4
from langchain.memory import ConversationBufferWindowMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessDomain(Enum):
    SALES = "sales"
    INVENTORY = "inventory"
    LOGISTICS = "logistics"
    PRODUCTION = "production"
    GENERAL = "general"
    UNKNOWN = "unknown"

class ScenarioType(Enum):
    PERFORMANCE_DECLINE = "performance_decline"
    INVENTORY_IMBALANCE = "inventory_imbalance"
    DELIVERY_ISSUES = "delivery_issues"
    CAPACITY_PLANNING = "capacity_planning"
    DEMAND_FORECASTING = "demand_forecasting"
    COST_OPTIMIZATION = "cost_optimization"
    WHAT_IF_ANALYSIS = "what_if_analysis"
    UNKNOWN = "unknown"

@dataclass
class WhatIfScenario:
    scenario_id: str
    description: str
    assumptions: Dict[str, Any]
    impact_areas: List[str]
    probability: float
    timestamp: str

    @classmethod
    def create(cls, description: str, assumptions: Dict[str, Any], impact_areas: List[str], probability: float):
        return cls(
            scenario_id=str(uuid4()),
            description=description,
            assumptions=assumptions,
            impact_areas=impact_areas,
            probability=probability,
            timestamp=datetime.now().isoformat()
        )

@dataclass
class ActionItem:
    action_id: str
    description: str
    priority: str
    impact: Dict[str, Any]
    dependencies: List[str]
    timeline: str
    status: str = "pending"

    @classmethod
    def create(cls, description: str, priority: str, impact: Dict[str, Any], dependencies: List[str], timeline: str):
        return cls(
            action_id=str(uuid4()),
            description=description,
            priority=priority,
            impact=impact,
            dependencies=dependencies,
            timeline=timeline
        )

@dataclass
class BusinessPlan:
    plan_id: str
    title: str
    summary: str
    actions: List[ActionItem]
    metrics: Dict[str, Any]
    timeline: str
    what_if_scenarios: List[WhatIfScenario] = field(default_factory=list)
    status: str = "draft"

    def to_markdown(self) -> str:
        md = f"""# {self.title}
## Executive Summary
{self.summary}
## Action Plan
"""
        for action in self.actions:
            md += f"""### {action.description}
- **Priority:** {action.priority}
- **Timeline:** {action.timeline}
- **Status:** {action.status}
- **Impact:**
"""
            for area, impact in action.impact.items():
                md += f"  - {area}: {impact}\n"
            md += "\n"
        md += "## Key Metrics\n"
        for metric, value in self.metrics.items():
            md += f"- **{metric}:** {value}\n"
        if self.what_if_scenarios:
            md += "\n## What-If Analysis\n"
            for scenario in self.what_if_scenarios:
                md += f"""### Scenario: {scenario.description}
- **Probability:** {scenario.probability * 100}%
- **Impact Areas:** {', '.join(scenario.impact_areas)}
- **Assumptions:**
"""
                for assumption, value in scenario.assumptions.items():
                    md += f"  - {assumption}: {value}\n"
                md += "\n"
        return md

@dataclass
class ReasoningStep:
    step_id: str
    observation: str
    thought: str
    action: Optional[str]
    result: Optional[str]
    timestamp: str

    @classmethod
    def create(cls, observation: str, thought: str, action: Optional[str] = None, result: Optional[str] = None):
        return cls(
            step_id=str(uuid4()),
            observation=observation,
            thought=thought,
            action=action,
            result=result,
            timestamp=datetime.now().isoformat()
        )

class ReActChain:
    def __init__(self):
        self.steps: List[ReasoningStep] = []
        self.start_time = datetime.now().isoformat()
        self.context = {}

    def add_step(self, observation: str, thought: str, action: Optional[str] = None, result: Optional[str] = None):
        step = ReasoningStep.create(observation, thought, action, result)
        self.steps.append(step)
        return step.step_id

    def to_dict(self) -> Dict:
        return {
            "start_time": self.start_time,
            "steps": [vars(step) for step in self.steps],
            "context": self.context
        }

class MainAgent:
    def __init__(self, api_key: str):
        self.llm_client = Groq(api_key=api_key)
        self.reasoning_chains: Dict[str, ReActChain] = {}
        self.active_plans: Dict[str, BusinessPlan] = {}
        self.memory = ConversationBufferWindowMemory(return_messages=True, k=10)  # Added LangChain memory
        self.system_prompt = """You are an intelligent business planning agent using the ReAct (Reasoning+Acting) pattern.
For each query:
1. Observe: Analyze the current situation
2. Think: Reason about implications and possibilities
3. Act: Suggest concrete actions
4. Reflect: Evaluate outcomes and adjust
5. If the prompt starts with what if or concludes to be a what-if analysis, analyse the previous original plan proposed based on the prompt of the user. Keep the same format of the output always
Format your response as:
{
    "reasoning_chain": [
        {
            "observation": "what you observe",
            "thought": "your reasoning",
            "action": "suggested action",
            "result": "expected outcome"
        }
    ],
    "business_plan": {
        "title": "plan title",
        "summary": "executive summary",
        "actions": [
            {
                "description": "action description",
                "priority": "HIGH|MEDIUM|LOW",
                "impact": {"area": "impact"},
                "dependencies": ["dependency1"],
                "timeline": "timeline"
            }
        ],
        "metrics": {"metric1": "value1"},
        "what_if_scenarios": [
            {
                "description": "scenario description",
                "assumptions": {"assumption1": "value1"},
                "impact_areas": ["area1", "area2"],
                "probability": 0.8
            }
        ]
    }
}"""

    def process_query(self, query: str, conversation_id: Optional[str] = None, continue_reasoning: bool = False) -> Dict:
        if not conversation_id:
            conversation_id = str(uuid4())

        try:
            if conversation_id not in self.reasoning_chains:
                self.reasoning_chains[conversation_id] = ReActChain()

            # Add query to memory
            self.memory.chat_memory.add_message({"role": "user", "content": query})

            context_prompt = query
            if continue_reasoning:
                previous_steps = self.reasoning_chains[conversation_id].to_dict()
                context_prompt = f"""Previous reasoning steps: {json.dumps(previous_steps)}
New query: {query}
Continue the reasoning process and update the business plan accordingly."""

            # Include memory in the context prompt
            memory_messages = [
                {"role": msg["role"], "content": msg["content"]} for msg in self.memory.load_memory_variables({})["history"]
            ]
            messages = [{"role": "system", "content": self.system_prompt}] + memory_messages + [{"role": "user", "content": context_prompt}]

            response = self.llm_client.chat.completions.create(
                messages=messages,
                model="llama3-8b-8192",
                temperature=0.7
            )
            result = json.loads(response.choices[0].message.content)

            # Update reasoning chain
            for step in result["reasoning_chain"]:
                self.reasoning_chains[conversation_id].add_step(
                    step["observation"],
                    step["thought"],
                    step.get("action"),
                    step.get("result")
                )

            # Create or update business plan
            plan_data = result["business_plan"]
            plan = BusinessPlan(
                plan_id=str(uuid4()) if conversation_id not in self.active_plans else self.active_plans[conversation_id].plan_id,
                title=plan_data["title"],
                summary=plan_data["summary"],
                actions=[ActionItem.create(**action) for action in plan_data["actions"]],
                metrics=plan_data["metrics"],
                timeline=datetime.now().isoformat(),
                what_if_scenarios=[WhatIfScenario.create(**scenario) for scenario in plan_data.get("what_if_scenarios", [])]
            )
            self.active_plans[conversation_id] = plan

            # Add AI response to memory
            self.memory.chat_memory.add_message({"role": "assistant", "content": json.dumps(result)})

            return {
                "conversation_id": conversation_id,
                "reasoning_chain": self.reasoning_chains[conversation_id].to_dict(),
                "plan_markdown": plan.to_markdown(),
                "raw_plan": vars(plan)
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "error": str(e),
                "reasoning_chain": self.reasoning_chains.get(conversation_id, ReActChain()).to_dict()
            }

    def what_if_analysis(self, conversation_id: str, scenario_description: str, assumptions: Dict[str, Any]) -> Dict:
        try:
            if conversation_id not in self.active_plans:
                raise ValueError("No active plan found for this conversation")

            prompt = f"""Analyze this what-if scenario for the existing plan:
Scenario: {scenario_description}
Assumptions: {json.dumps(assumptions)}
Current plan: {self.active_plans[conversation_id].to_markdown()}
Analyze the implications and suggest plan adjustments."""

            # Add what-if query to memory
            self.memory.chat_memory.add_message({"role": "user", "content": prompt})

            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
                temperature=0.7
            )
            result = json.loads(response.choices[0].message.content)

            # Update plan with new scenario
            plan = self.active_plans[conversation_id]
            for scenario in result["business_plan"].get("what_if_scenarios", []):
                plan.what_if_scenarios.append(WhatIfScenario.create(**scenario))

            # Update reasoning chain
            for step in result["reasoning_chain"]:
                self.reasoning_chains[conversation_id].add_step(
                    step["observation"],
                    step["thought"],
                    step.get("action"),
                    step.get("result")
                )

            # Add AI response to memory
            self.memory.chat_memory.add_message({"role": "assistant", "content": json.dumps(result)})

            return {
                "conversation_id": conversation_id,
                "reasoning_chain": self.reasoning_chains[conversation_id].to_dict(),
                "plan_markdown": plan.to_markdown(),
                "raw_plan": vars(plan)
            }

        except Exception as e:
            logger.error(f"Error in what-if analysis: {str(e)}")
            return {"error": str(e)}