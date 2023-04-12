# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        # Self-perceived healthcare assessment
        "start": "baseline_5_q1_healthcare",
        "questions": {
            "baseline_5_q1_healthcare": {
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
                "next": "baseline_5_q2_healthcare",
            },
            "baseline_5_q2_healthcare": {
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
                "next": None,
            },
        },
    },
}
