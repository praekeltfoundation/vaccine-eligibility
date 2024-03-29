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
                    ("half_of_the_days", "Half of the days"),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not_at_all": 0,
                    "several_days": 1,
                    "half_of_the_days": 2,
                    "nearly_every_day": 3,
                    "dont_understand": 3,
                    "skip_question": 3,
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
                    ("half_of_the_days", "Half of the days"),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not_at_all": 0,
                    "several_days": 1,
                    "half_of_the_days": 2,
                    "nearly_every_day": 3,
                    "dont_understand": 3,
                    "skip_question": 3,
                },
                "next": None,
            },
        },
    },
}
