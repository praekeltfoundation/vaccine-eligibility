# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Depression
    {
        "start": "endline_6_q1_depression",
        "questions": {
            "endline_6_q1_depression": {
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
                "next": "endline_6_q2_depression",
            },
            "endline_6_q2_depression": {
                "type": "list",
                "text": "Little interest or pleasure in doing things",
                "options": [
                    ("not_at_all", "Not at all"),
                    ("several_days", "Several days"),
                    (
                        "half_of_the_days",
                        "Half of the days",
                    ),
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
