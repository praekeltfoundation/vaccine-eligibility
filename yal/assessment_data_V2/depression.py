# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Depression
    {
        "start": "baseline_4_q1_depression",
        "questions": {
            "baseline_4_q1_depression": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Over the last 2 weeks, how often have you been "
                        "bothered by the following problems?*",
                        "",
                        "Feeling nervous, anxious or on edge",
                    ]
                ),
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_4_q2_depression",
            },
            "baseline_4_q2_depression": {
                "type": "list",
                "text": "\n".join(
                    [
                        "Not being able to stop or control worrying",
                    ]
                ),
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_4_q3_depression",
            },
            "baseline_4_q3_depression": {
                "type": "list",
                "text": "Feeling down, depressed or hopeless",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_4_q4_depression",
            },
            "baseline_4_q4_depression": {
                "type": "list",
                "text": "Little interest or pleasure in doing things",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": None,
            },
        },
    },
}
