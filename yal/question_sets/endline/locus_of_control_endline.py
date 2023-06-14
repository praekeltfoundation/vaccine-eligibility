# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    # A2
    "1": {
        "start": "endline_1_q1_loc",
        "questions": {
            "endline_1_q1_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I'm my own boss.* 😎",
                    ]
                ),
                "options": [
                    ("no_apply", "Does not apply"),
                    ("somewhat", "Applies somewhat"),
                    ("applies", "Applies"),
                    ("alot","Applies a lot"),
                    ("completely", "Applies completely"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "no_apply": 1,
                    "somewhat": 2,
                    "applies": 3,
                    "alot": 4,
                    "completely": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_1_q2_loc",
            },
            "endline_1_q2_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*If I work hard, I will be successful.* 🤓",
                    ]
                ),
                "options": [
                    ("no_apply", "Does not apply"),
                    ("somewhat", "Applies somewhat"),
                    ("applies", "Applies"),
                    ("alot","Applies a lot"),
                    ("completely", "Applies completely"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "no_apply": 1,
                    "somewhat": 2,
                    "applies": 3,
                    "alot": 4,
                    "completely": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_1_q3_loc",
            },
            "endline_1_q3_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*What I do mainly depends on other people.* 👯",
                    ]
                ),
                "options": [
                    ("no_apply", "Does not apply"),
                    ("somewhat", "Applies somewhat"),
                    ("applies", "Applies"),
                    ("alot","Applies a lot"),
                    ("completely", "Applies completely"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "no_apply": 5,
                    "somewhat": 4,
                    "applies": 3,
                    "alot": 2,
                    "completely": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_1_q4_loc",
            },
            "endline_1_q4_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Fate often gets in the way of my plans.*",
                    ]
                ),
                "options": [
                    ("no_apply", "Does not apply"),
                    ("somewhat", "Applies somewhat"),
                    ("applies", "Applies"),
                    ("alot","Applies a lot"),
                    ("completely", "Applies completely"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "no_apply": 5,
                    "somewhat": 4,
                    "applies": 3,
                    "alot": 2,
                    "completely": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": None,
            },
        },
    },
}
