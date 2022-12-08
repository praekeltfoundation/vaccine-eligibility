# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # A3 Depression and Anxiety
    {
        "start": "state_a3_start",
        "questions": {
            "state_a3_start": {
                "type": "info",
                "text": "\n".join(
                    [
                        "[persona_emoji] Think about the past 2 weeks...",
                        "",
                        "*Can you tell me how often you've been bothered "
                        "by any of the problems I'm about to mention.*",
                    ]
                ),
                "next": "state_a3_q1_depression",
            },
            "state_a3_q1_depression": {
                "text": "\n".join(
                    [
                        "Feeling nervous, anxious or on edge... 😰",
                    ]
                ),
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_a3_q2_depression",
            },
            "state_a3_q2_depression": {
                "text": "\n".join(
                    [
                        "Not being able to stop or control worrying... 😩",
                    ]
                ),
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_a3_q3_depression",
            },
            "state_a3_q3_depression": {
                "text": "Not being able to stop or control worrying... 😩",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_a3_q4_depression",
            },
            "state_a3_q4_depression": {
                "text": "Not having much interest or pleasure in doing things... 😑",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_a3_q5_depression",
            },
            "state_a3_q5_depression": {
                "text": "*Do you have someone to talk to when you have a worry or "
                "problem?*",
                "options": [
                    "Never",
                    "Some of the time",
                    "Most of the time",
                    "All the time",
                ],
                "next": None,
            },
        },
    },
}
