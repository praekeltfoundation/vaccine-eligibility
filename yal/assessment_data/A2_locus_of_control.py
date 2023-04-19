# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    # A2
    "1": {
        "start": "state_a2_1_q1_loc_of_ctrl",
        "questions": {
            "state_a2_1_q1_loc_of_ctrl": {
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
                "next": "state_a2_1_q2_loc_of_ctrl",
            },
            "state_a2_1_q2_loc_of_ctrl": {
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
                "next": "state_a2_1_q3_loc_of_ctrl",
            },
            "state_a2_1_q3_loc_of_ctrl": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I CAN get relevant health advice if and "
                        "when I want it. 👩🏾‍⚕️*",
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
                "next": "state_a2_1_q4_loc_of_ctrl",
            },
            "state_a2_1_q4_loc_of_ctrl": {
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
                "next": "state_a2_1_q5_loc_of_ctrl",
            },
            "state_a2_1_q5_loc_of_ctrl": {
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
