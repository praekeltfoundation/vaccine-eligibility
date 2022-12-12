# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A4 Connectedness
    {
        "start": "state_a4_q1_connectedness",
        "questions": {
            "state_a4_q1_connectedness": {
                "type": "list",
                "text": "\n".join(
                    [
                        "[persona_emoji] *Do you have someone to talk to when you "
                        "have a worry or problem?*",
                    ]
                ),
                "options": [
                    "Never",
                    "Sometimes",
                    "Most of the time",
                    "All the time",
                ],
                "next": None,
            },
        },
    },
}
