# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1": {
        "start": "state_a2_3_q1_self_esteem",
        "questions": {
            "state_a2_3_q1_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I feel that I am a person who has worth — at least as much "
                        "worth as others.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                },
                "next": "state_a2_3_q2_self_esteem",
            },
            "state_a2_3_q2_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I feel like I have quite a few of good qualities.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                },
                "next": "state_a2_3_q3_self_esteem",
            },
            "state_a2_3_q3_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*In general, I tend to feel like a failure.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 0,
                    "agree": 1,
                    "disagree": 2,
                    "strongly_disagree": 3,
                },
                "next": "state_a2_3_q4_self_esteem",
            },
            "state_a2_3_q4_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I feel like I don't have much to be proud of.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 0,
                    "agree": 1,
                    "disagree": 2,
                    "strongly_disagree": 3,
                },
                "next": "state_a2_3_q5_self_esteem",
            },
            "state_a2_3_q5_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I have a positive attitude toward myself.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                },
                "next": "state_a2_3_q6_self_esteem",
            },
            "state_a2_3_q6_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I'm generally satisfied with myself.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 3,
                    "agree": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                },
                "next": "state_a2_3_q7_self_esteem",
            },
            "state_a2_3_q7_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I wish I could have more respect for myself.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 0,
                    "agree": 1,
                    "disagree": 2,
                    "strongly_disagree": 3,
                },
                "next": "state_a2_3_q8_self_esteem",
            },
            "state_a2_3_q8_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*I definitely feel useless at times.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 0,
                    "agree": 1,
                    "disagree": 2,
                    "strongly_disagree": 3,
                },
                "next": "state_a2_3_q9_self_esteem",
            },
            "state_a2_3_q9_self_esteem": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*Sometimes I think I'm no good at all.*_",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "scoring": {
                    "strongly_agree": 0,
                    "agree": 1,
                    "disagree": 2,
                    "strongly_disagree": 3,
                },
                "next": "state_a2_3_final",
            },
            "state_a2_3_final": {
                "type": "info",
                "text": "\n".join(
                    [
                        "🏁 🎉",
                        "",
                        "[persona_emoji] Yoh! That was hella questions and a "
                        "looot of personal and sensitive stuff too, eh?",
                        "",
                        "Thanks so much — proud of you for pushing through. 💪",
                    ]
                ),
                "next": None,
            },
        },
    },
}
