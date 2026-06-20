from functools import partial
from typing import Any

from langgraph.graph import END, StateGraph

from qa_testgen.agents.pytest_generator import PytestGeneratorAgent
from qa_testgen.agents.scenario_generator import ScenarioGeneratorAgent
from qa_testgen.agents.scenario_validator import ScenarioValidatorAgent
from qa_testgen.agents.syntax_validator import SyntaxValidatorAgent
from qa_testgen.config.settings import AppSettings
from qa_testgen.domain.state import GraphState
from qa_testgen.graph.nodes import (
    generate_pytest_node,
    generate_scenarios_node,
    repair_pytest_node,
    save_artifacts_node,
    validate_scenarios_node,
    validate_syntax_node,
)
from qa_testgen.graph.routers import (
    route_after_scenario_validation,
    route_after_syntax_validation,
)
from qa_testgen.services.artifact_store import ArtifactStore


class TestGenerationGraphBuilder:
    def __init__(
        self,
        scenario_generator: ScenarioGeneratorAgent,
        scenario_validator: ScenarioValidatorAgent,
        pytest_generator: PytestGeneratorAgent,
        syntax_validator: SyntaxValidatorAgent,
        settings: AppSettings,
        artifact_store: ArtifactStore,
    ) -> None:
        self.scenario_generator = scenario_generator
        self.scenario_validator = scenario_validator
        self.pytest_generator = pytest_generator
        self.syntax_validator = syntax_validator
        self.settings = settings
        self.artifact_store = artifact_store

    def build(self) -> Any:
        graph = StateGraph(GraphState)
        graph.add_node(
            "generate_scenarios",
            partial(generate_scenarios_node, agent=self.scenario_generator),
        )
        graph.add_node(
            "validate_scenarios",
            partial(validate_scenarios_node, agent=self.scenario_validator),
        )
        graph.add_node(
            "generate_pytest",
            partial(generate_pytest_node, agent=self.pytest_generator),
        )
        graph.add_node(
            "validate_syntax",
            partial(validate_syntax_node, agent=self.syntax_validator),
        )
        graph.add_node(
            "repair_pytest",
            partial(repair_pytest_node, agent=self.pytest_generator),
        )
        graph.add_node(
            "save_artifacts",
            partial(save_artifacts_node, artifact_store=self.artifact_store),
        )
        graph.set_entry_point("generate_scenarios")
        graph.add_edge("generate_scenarios", "validate_scenarios")
        graph.add_conditional_edges(
            "validate_scenarios",
            partial(route_after_scenario_validation, settings=self.settings),
            {
                "generate_scenarios": "generate_scenarios",
                "generate_pytest": "generate_pytest",
            },
        )
        graph.add_edge("generate_pytest", "validate_syntax")
        graph.add_conditional_edges(
            "validate_syntax",
            partial(route_after_syntax_validation, settings=self.settings),
            {
                "repair_pytest": "repair_pytest",
                "save_artifacts": "save_artifacts",
            },
        )
        graph.add_edge("repair_pytest", "validate_syntax")
        graph.add_edge("save_artifacts", END)
        return graph.compile()
