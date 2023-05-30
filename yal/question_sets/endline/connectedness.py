# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A4 Connectedness
    {
        "start": "endline_3_q1_connectedness",
        "questions": {
            "endline_2_q1_connectedness": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you have someone to talk to when you have a "
                        "worry or problem?*",
                    ]
                ),
                "options": [
                    ("never", "Never"),
                    ("some_of_the_time", "Some of the time"),
                    ("most_of_the_time", "Most of the time"),
                    ("all_of_the_time", "All of the time"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "never": 0,
                    "some_of_the_time": 1,
                    "most_of_the_time": 2,
                    "all_of_the_time": 3,
                    "dont_understand": 0,
                    "skip_question": 0,
                },
                "next": None,
            },
        },
    },
}
