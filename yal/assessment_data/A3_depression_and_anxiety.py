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
                        "*Over the last two weeks, how often have you been bothered "
                        "by the following problems?*",
                    ]
                ),
                "next": "state_a3_q1_depression",
            },
            "state_a3_q1_depression": {
                "type": "list",
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
                "scoring": {
                    "not_at_all": 5,
                    "several_days": 3,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                },
                "next": "state_a3_q2_depression",
            },
            "state_a3_q2_depression": {
                "type": "list",
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
                "scoring": {
                    "not_at_all": 5,
                    "several_days": 3,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                },
                "next": "state_a3_q3_depression",
            },
            "state_a3_q3_depression": {
                "type": "list",
                "text": "Feeling down, depressed or hopeless 😔",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "scoring": {
                    "not_at_all": 5,
                    "several_days": 3,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                },
                "next": "state_a3_q4_depression",
            },
            "state_a3_q4_depression": {
                "type": "list",
                "text": "Not having much interest or pleasure in doing things... 😑",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "scoring": {
                    "not_at_all": 5,
                    "several_days": 3,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                },
                "next": None,
            },
        },
    },
}
