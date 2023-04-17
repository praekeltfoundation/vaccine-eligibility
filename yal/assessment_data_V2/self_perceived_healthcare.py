# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        # Self-perceived healthcare assessment
        "start": "baseline_6_q1_healthcare",
        "questions": {
            "baseline_6_q1_healthcare": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How good a job do you feel you are doing in taking "
                        "care of your health?*",
                    ]
                ),
                "options": [
                    ("excellent", "Excellent"),
                    ("very_good", "Very Good"),
                    ("good", "Good"),
                    ("fair", "Fair"),
                    ("poor", "Poor"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "excellent": 5,
                    "very_good": 4,
                    "good": 3,
                    "fair": 2,
                    "poor": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "baseline_6_q2_healthcare",
            },
            "baseline_6_q2_healthcare": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*When you have a health need (e.g. contraception, "
                        "flu symptoms), do you go to your closest clinic?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("sometimes", "Sometimes"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "sometimes": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": None,
            },
        },
    },
}
