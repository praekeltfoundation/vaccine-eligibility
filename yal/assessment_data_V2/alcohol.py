# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Alcohol
    {
        "start": "baseline_10_q1_alcohol",
        "questions": {
            "baseline_10_q1_alcohol": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Have you ever felt guilty about drinking or drug use?* 🍻💉",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_10_q2_alcohol",
            },
            "baseline_10_q2_alcohol": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Have you ever felt you needed to cut down on your "
                        "drinking or drug use?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_10_q3_alcohol",
            },
            "baseline_10_q3_alcohol": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Have people annoyed you by criticising your drinking "
                        "or drug use?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_10_q4_alcohol",
            },
            "baseline_10_q4_alcohol": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Have you ever felt you needed a drink or used drugs "
                        "first thing in the morning (eye‐opener)?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": None,
            },
        },
    },
}
