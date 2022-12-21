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
                        "_*I'm my own boss.*_ 😎",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q2_loc_of_ctrl",
            },
            "state_a2_1_q2_loc_of_ctrl": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*If I work hard, I will be successful.*_ 🤓",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q3_loc_of_ctrl",
            },
            "state_a2_1_q3_loc_of_ctrl": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I CAN get relevant health advice if and "
                        "when I want it. 👩🏾‍⚕️*_",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q4_loc_of_ctrl",
            },
            "state_a2_1_q4_loc_of_ctrl": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*What I do mainly depends on other people.*_ 👯",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q5_loc_of_ctrl",
            },
            "state_a2_1_q5_loc_of_ctrl": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*Fate often gets in the way of my plans.*_",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": None,
            }
        },
    },
}
