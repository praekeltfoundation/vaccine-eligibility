# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A6 Body Image
    {
        "start": "state_a6_q1_body_image",
        "questions": {
            "state_a6_q1_body_image": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*_I feel good about myself._*",
                    ]
                ),
                "options": [
                    "Yes",
                    "No",
                    "Sometimes",
                ],
                "scoring": {"yes": 5, "no": 0, "sometimes": 3},
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
                    "Yes",
                    "No",
                    "Sometimes",
                ],
                "scoring": {"yes": 5, "no": 0, "sometimes": 3},
                "next": None,
            },
        },
    },
}
