# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A5 Gender Attitude
    {
        "start": "state_a5_q1_gender_attitude",
        "questions": {
            "state_a5_q1_gender_attitude": {
                "text": "\n".join(
                    [
                        "*_There are times when a woman deserves to be beaten._*",
                    ]
                ),
                "options": [
                    "Strongly Agree",
                    "Kinda Agree",
                    "Do not Agree",
                ],
                "next": "state_a5_q2_gender_attitude",
            },
            "state_a5_q2_gender_attitude": {
                "text": "\n".join(
                    [
                        "*_It's a woman's responsibility to avoid getting pregnant._*",
                    ]
                ),
                "options": [
                    "Strongly Agree",
                    "Kinda Agree",
                    "Do not Agree",
                ],
                "next": "state_a5_q3_gender_attitude",
            },
            "state_a5_q3_gender_attitude": {
                "text": "\n".join(
                    [
                        "*_A man and a woman should decide together what type of "
                        "contraceptive to use_*",
                    ]
                ),
                "options": [
                    "Strongly Agree",
                    "Kinda Agree",
                    "Do not Agree",
                ],
                "next": "state_a5_q4_gender_attitude",
            },
            "state_a5_q4_gender_attitude": {
                "text": "\n".join(
                    [
                        "*_If a guy gets women pregnant, the child is the "
                        "responsibility of both._*",
                    ]
                ),
                "options": [
                    "Strongly Agree",
                    "Kinda Agree",
                    "Do not Agree",
                ],
                "next": None,
            },
        },
    },
}
