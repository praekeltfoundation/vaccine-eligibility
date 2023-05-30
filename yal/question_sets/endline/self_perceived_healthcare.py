# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        # Self-perceived healthcare assessment
        "start": "endline_6_q1_self_perceived_healthcare",
        "questions": {
            "endline_6_q1_self_perceived_healthcare": {
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
                "next": "endline_6_q2_self_perceived_healthcare",
            },
            "endline_6_q2_self_perceived_healthcare": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*In the past 7 days, how many days did you go hungry?*",
                    ]
                ),
                "options": [
                    ("none", "None"),
                    ("1_2", "1-2"),
                    ("3_4", "3-4"),
                    ("5_7", "5-7"),
                    ("rather_not_say", "Rather not say"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "none": 0,
                    "1_2": 0,
                    "3_4": 0,
                    "5_7": 0,
                    "rather_not_say": 0,
                    "skip_question": 0,
                },
                "next": "endline_6_q3_self_perceived_healthcare",
            },
            "endline_6_q3_self_perceived_healthcare": {
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
