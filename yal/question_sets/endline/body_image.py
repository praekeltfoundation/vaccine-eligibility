# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        "start": "endline_8_q1_body_image",
        "questions": {
            "endline_8_q1_body_image": {
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
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 3,
                    "no": 1,
                    "sometimes": 2,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q2_body_image",
            },
            "endline_8_q2_body_image": {
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
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 3,
                    "no": 1,
                    "sometimes": 2,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": None,
            },
        },
    },
}
