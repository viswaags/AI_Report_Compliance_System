class CommunicationAgent:

    def generate_email_draft(
        self,
        feedback,
        report,
        event
    ):

        event_title = (
            event.get("event_title")
            if event else "Event"
        )

        return {
            "email_subject":
                f"Report Corrections Required - {event_title}",

            "email_body":
                (
                    "Dear Student Representative,\n\n"
                    "The submitted report requires corrections "
                    "before it can proceed for approval.\n\n"
                    f"{feedback}\n\n"
                    "Please revise the report and resubmit.\n\n"
                    "Regards,\n"
                    "AI Report Compliance System"
                )
        }