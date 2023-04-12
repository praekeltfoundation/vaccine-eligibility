# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        "start": "baseline_3_q1_body_image",
        "questions": {
            "baseline_3_q1_body_image": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you agree with this statement?*",
                        "",
                        "I feel good about myself.",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("sometimes", "Sometimes"),
                    ("dont_understand", "I don't understand"),
                    ("skip", "Skip"),
                ],
                "scoring": {
                    "yes": 3,
                    "no": 1,
                    "sometimes": 2,
                    "dont_understand": 1,
                    "skip": 1,
                },
                "next": "baseline_3_q2_body_image",
            },
            "baseline_3_q2_body_image": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you agree with this statement?*",
                        "",
                        "I feel good about my body.",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("sometimes", "Sometimes"),
                    ("dont_understand", "I don't understand"),
                    ("skip", "Skip"),
                ],
                "scoring": {
                    "yes": 3,
                    "no": 1,
                    "sometimes": 2,
                    "dont_understand": 1,
                    "skip": 1,
                },
                "next": None,
            },
        },
    },
}
