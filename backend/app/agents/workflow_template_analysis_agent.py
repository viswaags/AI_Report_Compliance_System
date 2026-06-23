from app.agents.template_agent import (
    TemplateAgent
)


class WorkflowTemplateAnalysisAgent:

    @staticmethod
    def run(state):

        analysis = (
            TemplateAgent.analyze_template(
                file_path=state["file_path"],
                version=state["version"]
            )
        )

        state["template_analysis"] = analysis

        print("Template analysis completed.")

        return state