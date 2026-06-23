from langgraph.graph import (
    StateGraph,
    END
)

from app.workflows.template_state import (
    TemplateWorkflowState
)

from app.agents.workflow_template_analysis_agent import (
    WorkflowTemplateAnalysisAgent
)

from app.agents.workflow_template_validation_agent import (
    WorkflowTemplateValidationAgent
)

from app.agents.workflow_template_version_agent import (
    WorkflowTemplateVersionAgent
)

from app.agents.workflow_template_storage_agent import (
    WorkflowTemplateStorageAgent
)


class TemplateWorkflow:

    @staticmethod
    def build():

        graph = StateGraph(
            TemplateWorkflowState
        )

        graph.add_node(
            "analysis",
            WorkflowTemplateAnalysisAgent.run
        )

        graph.add_node(
            "validation",
            WorkflowTemplateValidationAgent.run
        )

        graph.add_node(
            "version",
            WorkflowTemplateVersionAgent.run
        )

        graph.add_node(
            "storage",
            WorkflowTemplateStorageAgent.run
        )

        graph.set_entry_point(
            "analysis"
        )

        graph.add_edge(
            "analysis",
            "validation"
        )

        graph.add_edge(
            "validation",
            "version"
        )

        graph.add_edge(
            "version",
            "storage"
        )

        graph.add_edge(
            "storage",
            END
        )

        return graph.compile()