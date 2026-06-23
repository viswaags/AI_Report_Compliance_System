class WorkflowReviewDecisionAgent:

    @staticmethod
    def route(state):

        review = state["review"]

        if review.status == "APPROVED":
            return "approved"

        return "revision_required"