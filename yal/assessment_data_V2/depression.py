# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
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
                        "Feeling down, depressed or hopeless",
                    ]
                ),
                "options": [
                    ("not_at_all", "Not at all"),
                    ("several_days", "Several days"),
                    ("more_than_half", "More than half the days"),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip", "Skip"),
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
                "text": "Little interest or pleasure in doing things",
                "options": [
                    ("not_at_all", "Not at all"),
                    ("several_days", "Several days"),
                    (
                        "more_than_half_the_days_this_can_be_super_long_as_long",
                        "More t half the days",
                    ),
                    ("nearly_every_day", "Nearly every day"),
                    ("dont_understand", "I don't understand"),
                    ("skip", "Skip"),
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
