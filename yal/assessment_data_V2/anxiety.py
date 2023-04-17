# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Anxiety
    {
        "start": "baseline_5_q1_anxiety",
        "questions": {
            "baseline_5_q1_anxiety": {
                "type": "list",
                "text": "Feeling nervous, anxious or on edge",
                "options": [
                    ("not_at_all", "Not at all"),
                    ("several_days", "Several days"),
                    ("more_than_half_the_days", "More than half the days"),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip_question": 0,
                },
                "next": "baseline_5_q2_anxiety",
            },
            "baseline_5_q2_anxiety": {
                "type": "list",
                "text": "\n".join(
                    [
                        "Not being able to stop or control worrying",
                    ]
                ),
                "options": [
                    ("not_at_all", "Not at all"),
                    ("several_days", "Several days"),
                    ("more_than_half_the_days", "More than half the days"),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not_at_all": 3,
                    "several_days": 2,
                    "more_than_half_the_days": 1,
                    "nearly_every_day": 0,
                    "dont_understand": 0,
                    "skip_question": 0,
                },
                "next": None,
            },
        },
    },
}
