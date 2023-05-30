# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    # A2
    "1": {
        "start": "endline_2_q1_loc",
        "questions": {
            "endline_2_q1_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I'm my own boss.* 😎",
                    ]
                ),
                "options": [
                    "Does not apply",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                    "I don't understand",
                    "Skip question",
                ],
                "next": "endline_2_q2_loc",
            },
            "endline_2_q2_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*If I work hard, I will be successful.* 🤓",
                    ]
                ),
                "options": [
                    "Does not apply",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                    "I don't understand",
                    "Skip question",
                ],
                "next": "endline_2_q3_loc",
            },
            "endline_2_q3_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*What I do mainly depends on other people.* 👯",
                    ]
                ),
                "options": [
                    "Does not apply",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                    "I don't understand",
                    "Skip question",
                ],
                "next": "endline_2_q4_loc",
            },
            "endline_2_q4_loc": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Fate often gets in the way of my plans.*",
                    ]
                ),
                "options": [
                    "Does not apply",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                    "I don't understand",
                    "Skip question",
                ],
                "next": None,
            },
        },
    },
}
