# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A4 Connectedness
    {
        "start": "state_baseline_q1_connectedness",
        "questions": {
            "state_baseline_q1_connectedness": {
                "type": "list",
                "text": "\n".join(
                    [
                        "[persona_emoji] BASELINE*Do you have someone to talk to when you "
                        "have a worry or problem?*",
                    ]
                ),
                "options": [
                    "Never",
                    "Sometimes",
                    "Most of the time",
                    "All the time",
                ],
                "scoring": {
                    "never": 0,
                    "sometimes": 1,
                    "most_of_the_time": 3,
                    "all_the_time": 5,
                },
                "next": None,
            },
        },
    },
}
