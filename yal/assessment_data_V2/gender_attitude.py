# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Gender Attitude
    {
        "start": "baseline_8_q1_gender_attitude",
        "questions": {
            "baseline_8_q1_gender_attitude": {
                "type": "list",
                "text": "\n".join(
                    [
                        "**How do you feel about each of the following "
                        "statements?* *",
                        "",
                        "There are times when a woman deserves to be beaten",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("somewhat_agree", "Somewhat agree"),
                    ("disagree", "Disagree"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 1,
                    "somewhat_agree": 2,
                    "disagree": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_8_q2_gender_attitude",
            },
            "baseline_8_q2_gender_attitude": {
                "type": "list",
                "text": "\n".join(
                    [
                        "It’s a woman’s responsibility to avoid getting pregnant.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("somewhat_agree", "Somewhat agree"),
                    ("disagree", "Disagree"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 1,
                    "somewhat_agree": 2,
                    "disagree": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_8_q3_gender_attitude",
            },
            "baseline_8_q3_gender_attitude": {
                "type": "list",
                "text": "\n".join(
                    [
                        "A man and a woman should decide together what type "
                        "of contraceptive to use.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("somewhat_agree", "Somewhat agree"),
                    ("disagree", "Disagree"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 1,
                    "somewhat_agree": 2,
                    "disagree": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_8_q4_gender_attitude",
            },
            "baseline_8_q4_gender_attitude": {
                "type": "list",
                "text": "\n".join(
                    [
                        "If a guy gets a women pregnant, the child is "
                        "responsibility of both.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("somewhat_agree", "Somewhat agree"),
                    ("disagree", "Disagree"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 1,
                    "somewhat_agree": 2,
                    "disagree": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": None,
            },
        },
    },
}
