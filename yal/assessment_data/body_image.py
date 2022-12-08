# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "8":
    # A6 Body Image
    {
        "start": "state_a6_start",
        "questions": {
            "state_a6_start": {
                "type": "button",
                "text": "\n".join(
                    [
                        "[persona_emoji]  *Let me know how you feel about these next "
                        "few statements.*",
                        "",
                        "There are no right or wrong answers. Try and answer "
                        "honestly and freely as you can.",
                        "",
                        "Remember — everything stays between us! 🤐",
                        "",
                    ]
                ),
                "options": ["OK, let's do it!"],
                "next": "state_a6_q1_body_image",
            },
            "state_a6_q1_body_image": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*_I feel good about myself._*",
                    ]
                ),
                "options": [
                    "Strongly Agree",
                    "Kinda Agree",
                    "Do not Agree",
                ],
                "next": "state_a6_q2_body_image",
            },
            "state_a6_q2_body_image": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*_I feel good about my body._*",
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
