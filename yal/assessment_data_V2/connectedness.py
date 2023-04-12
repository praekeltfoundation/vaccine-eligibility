# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A4 Connectedness
    {
        "start": "baseline_2_q1_connectedness",
        "questions": {
            "baseline_2_q1_connectedness": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you have someone to talk to when you have a ",
                        "worry or problem?*",
                    ]
                ),
                "options": [
                    "Never",
                    "Some of the time",
                    "Most of the time",
                    "All of the time",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "never": 0,
                    "some_of_the_time": 1,
                    "most_of_the_time": 2,
                    "all_of_the_time": 3,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": None,
            },
        },
    },
}
