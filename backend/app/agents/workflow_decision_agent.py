class WorkflowDecisionAgent:

    @staticmethod
    def route(state):

        validation = state["validation"]

        if validation["status"] == "passed":
            return "passed"

        return "failed"