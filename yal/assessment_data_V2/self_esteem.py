# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        "start": "baseline_1_q1_self_esteem",
        "questions": {
            "baseline_1_q1_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "How do you feel about the following statements?",
                        "",
                        "*I feel that I am a person who has worth — at least as much "
                        "worth as others.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q2_self_esteem",
            },
            "baseline_1_q2_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I feel that I have a number of good qualities.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q3_self_esteem",
            },
            "baseline_1_q3_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*All in all, I am inclined to feel that I am " "a failure.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q4_self_esteem",
            },
            "baseline_1_q4_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I am able to do things as well as most other people.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q5_self_esteem",
            },
            "baseline_1_q5_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I feel I do not have much to be proud of.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q6_self_esteem",
            },
            "baseline_1_q6_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I take a positive attitude toward myself.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q7_self_esteem",
            },
            "baseline_1_q7_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*On the whole, I am satisfied with myself.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q8_self_esteem",
            },
            "baseline_1_q8_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I wish I could have more respect for myself.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_q9_self_esteem",
            },
            "baseline_1_q9_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*I certainly feel useless at times.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": "baseline_1_final",
            },
            "baseline_1_q10_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*At times I think I am no good at all.*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                    "I don't understand",
                    "Skip",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                    "dont_understand": 0,
                    "skip": 0,
                },
                "next": None,
            },
        },
    },
}
