from langgraph.graph import (
    StateGraph,
    END
)

from app.workflows.state import (
    ReportWorkflowState
)

from app.agents.document_processing_agent import (
    DocumentProcessingAgent
)

from app.agents.workflow_extraction_storage_agent import (
    WorkflowExtractionStorageAgent
)

from app.agents.compliance_agent import (
    ComplianceAgent
)

from app.agents.workflow_semantic_agent import (
    WorkflowSemanticAgent
)

from app.agents.workflow_validation_result_agent import (
    WorkflowValidationResultAgent
)

from app.agents.workflow_status_agent import (
    WorkflowStatusAgent
)

from app.agents.workflow_feedback_agent import (
    WorkflowFeedbackAgent
)

from app.agents.workflow_communication_agent import (
    WorkflowCommunicationAgent
)

from app.agents.workflow_notification_agent import (
    WorkflowNotificationAgent
)

from app.agents.workflow_decision_agent import (
    WorkflowDecisionAgent
)


class ReportWorkflow:

    @staticmethod
    def build():

        graph = StateGraph(
            ReportWorkflowState
        )

        #
        # Nodes
        #

        graph.add_node(
            "document",
            DocumentProcessingAgent.run
        )

        graph.add_node(
            "extraction_storage",
            WorkflowExtractionStorageAgent.run
        )

        graph.add_node(
            "compliance",
            ComplianceAgent.run
        )

        graph.add_node(
            "semantic",
            WorkflowSemanticAgent.run
        )

        graph.add_node(
            "validation_result",
            WorkflowValidationResultAgent.run
        )

        graph.add_node(
            "status",
            WorkflowStatusAgent.run
        )

        graph.add_node(
            "feedback",
            WorkflowFeedbackAgent.run
        )

        graph.add_node(
            "communication",
            WorkflowCommunicationAgent.run
        )

        graph.add_node(
            "notification",
            WorkflowNotificationAgent.run
        )

        #
        # Entry Point
        #

        graph.set_entry_point(
            "document"
        )

        #
        # Main Validation Flow
        #

        graph.add_edge(
            "document",
            "extraction_storage"
        )

        graph.add_edge(
            "extraction_storage",
            "compliance"
        )

        graph.add_edge(
            "compliance",
            "semantic"
        )

        graph.add_edge(
            "semantic",
            "validation_result"
        )

        graph.add_edge(
            "validation_result",
            "status"
        )

        #
        # Pass / Fail Decision
        #

        graph.add_conditional_edges(
            "status",
            WorkflowDecisionAgent.route,
            {
                "passed":
                    "notification",

                "failed":
                    "feedback"
            }
        )

        #
        # Failed Path
        #

        graph.add_edge(
            "feedback",
            "communication"
        )

        graph.add_edge(
            "communication",
            "notification"
        )

        #
        # Exit
        #

        graph.add_edge(
            "notification",
            END
        )

        return graph.compile()