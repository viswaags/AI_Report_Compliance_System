from langgraph.graph import StateGraph
from langgraph.graph import END

from app.workflows.state import (
    ReportWorkflowState
)

from app.agents.document_processing_agent import (
    DocumentProcessingAgent
)

from app.agents.compliance_agent import (
    ComplianceAgent
)

from app.agents.workflow_feedback_agent import (
    WorkflowFeedbackAgent
)

from app.agents.workflow_communication_agent import (
    WorkflowCommunicationAgent
)


class ReportWorkflow:

    @staticmethod
    def build():

        graph = StateGraph(
            ReportWorkflowState
        )

        graph.add_node(
            "document",
            DocumentProcessingAgent.run
        )

        graph.add_node(
            "compliance",
            ComplianceAgent.run
        )

        graph.add_node(
            "feedback",
            WorkflowFeedbackAgent.run
        )

        graph.add_node(
            "communication",
            WorkflowCommunicationAgent.run
        )

        graph.set_entry_point(
            "document"
        )

        graph.add_edge(
            "document",
            "compliance"
        )

        graph.add_edge(
            "compliance",
            "feedback"
        )

        graph.add_edge(
            "feedback",
            "communication"
        )

        graph.add_edge(
            "communication",
            END
        )

        return graph.compile()