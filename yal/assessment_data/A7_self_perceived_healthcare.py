# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        # A2.2 Self-perceived healthcare assessment
        "start": "state_a2_2_q5_healthcare",
        "questions": {
            "state_a2_2_q5_healthcare": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*When I have health needs (like  contraception or "
                        "flu symptoms), I go to my closest clinic. 🏥*",
                    ]
                ),
                "options": [
                    "Yes",
                    "No",
                    "Sometimes",
                ],
                "scoring": {
                    "yes": 5,
                    "no": 0,
                    "sometimes": 3,
                },
                "next": "state_a2_2_q6_healthcare",
            },
            "state_a2_2_q6_healthcare": {
                "type": "list",
                "text": "\n".join(
                    [
                        "[persona_emoji]  How good a job do you feel you are doing "
                        "in taking care of your health?",
                    ]
                ),
                "options": [
                    "Excellent",
                    "Very Good",
                    "Good",
                    "OK",
                    "Pretty bad",
                ],
                "scoring": {
                    "excellent": 5,
                    "very_good": 4,
                    "good": 3,
                    "ok": 2,
                    "pretty_bad": 1,
                },
                "next": "state_a2_2_q7_healthcare",
            },
            "state_a2_2_final": {
                "type": "info",
                "text": "\n".join(
                    [
                        "[persona_emoji]  Fantastic! That's it.",
                        "",
                        "I'll chat with you again tomorrow.",
                    ]
                ),
                "next": None,
            },
        },
    },
}
