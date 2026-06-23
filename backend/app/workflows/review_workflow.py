from langgraph.graph import (
    StateGraph,
    END
)

from app.workflows.review_state import (
    ReviewWorkflowState
)

from app.agents.workflow_review_agent import (
    WorkflowReviewAgent
)

from app.agents.workflow_event_record_agent import (
    WorkflowEventRecordAgent
)

from app.agents.workflow_review_decision_agent import (
    WorkflowReviewDecisionAgent
)

from app.agents.workflow_review_notification_agent import (
    WorkflowReviewNotificationAgent
)

from app.agents.workflow_review_communication_agent import (
    WorkflowReviewCommunicationAgent
)


class ReviewWorkflow:

    @staticmethod
    def build():

        graph = StateGraph(
            ReviewWorkflowState
        )

        graph.add_node(
            "review",
            WorkflowReviewAgent.run
        )

        graph.add_node(
            "event_record",
            WorkflowEventRecordAgent.run
        )

        graph.add_node(
            "notification",
            WorkflowReviewNotificationAgent.run
        )

        graph.add_node(
            "communication",
            WorkflowReviewCommunicationAgent.run
        )

        graph.set_entry_point(
            "review"
        )

        graph.add_conditional_edges(
            "review",
            WorkflowReviewDecisionAgent.route,
            {
                "approved":
                    "event_record",

                "revision_required":
                    "notification"
            }
        )

        graph.add_edge(
            "event_record",
            "notification"
        )

        graph.add_edge(
            "notification",
            "communication"
        )

        graph.add_edge(
            "communication",
            END
        )

        return graph.compile()