# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    # A2
    "1": {
        # A2.1 Locus of Control
        "start": "state_a2_1_q1_loc_of_ctrl",
        "questions": {
            "state_a2_1_q1_loc_of_ctrl": {
                "text": "\n".join(
                    [
                        "_*I'm my own boss.*_ 😎",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q2_loc_of_ctrl",
            },
            "state_a2_1_q2_loc_of_ctrl": {
                "text": "\n".join(
                    [
                        "_*If I work hard, I will be successful.*_ 🤓",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q3_loc_of_ctrl",
            },
            "state_a2_1_q3_loc_of_ctrl": {
                "text": "\n".join(
                    [
                        "_*I CAN get relevant health advice if and "
                        "when I want it. 👩🏾‍⚕️*_",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q4_loc_of_ctrl",
            },
            "state_a2_1_q4_loc_of_ctrl": {
                "text": "\n".join(
                    [
                        "_*What I do mainly depends on other people.*_ 👯",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_q5_loc_of_ctrl",
            },
            "state_a2_1_q5_loc_of_ctrl": {
                "text": "\n".join(
                    [
                        "_*Fate often gets in the way of my plans.*_",
                    ]
                ),
                "options": [
                    "Not at all true",
                    "A little true",
                    "Kind of true",
                    "Very true",
                    "Extremely True",
                ],
                "next": "state_a2_1_final",
            },
            "state_a2_1_final": {
                "type": "info",
                "text": "\n".join(
                    [
                        "[persona_emoji] Thanks, that was great! "
                        "And what about your health...?",
                    ]
                ),
                "next": None,
            },
        },
    },
    "2": {
        # A2.2 Self-perceived healthcare assessment
        "start": "state_a2_2_q5_healthcare",
        "questions": {
            "state_a2_2_q5_healthcare": {
                "text": "\n".join(
                    [
                        "*When I have health needs (like  contraception or "
                        "flu symptoms), I go to my closest clinic. 🏥*",
                    ]
                ),
                "options": [
                    "Yes",
                    "No",
                    "Sometimes",
                ],
                "next": "state_a2_2_q6_healthcare",
            },
            "state_a2_2_q6_healthcare": {
                "text": "\n".join(
                    [
                        "[persona_emoji]  How good a job would you say you do "
                        "when it comes to taking care of your health?",
                    ]
                ),
                "options": [
                    "Excellent",
                    "Very Good",
                    "Good",
                    "OK",
                    "Pretty bad",
                ],
                "next": "state_a2_2_q7_healthcare",
            },
            "state_a2_2_final": {
                "type": "info",
                "text": "\n".join(
                    [
                        "[persona_emoji]  Fantastic! OK, we're almost done.",
                        "",
                        "This last bunch of questions is to figure out how "
                        "you feel about yourself right now.",
                        "",
                        "You know the dance 😉 — for each statement, I just need you "
                        "to choose an answer that matches how you feel about it.",
                    ]
                ),
                "next": None,
            },
        },
    },
    "3": {
        # A2.3 Self-esteem assessment
        "start": "state_a2_3_q1_self_esteem",
        "questions": {
            "state_a2_3_q1_self_esteem": {
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
                "next": "state_a2_3_q2_self_esteem",
            },
            "state_a2_3_q2_self_esteem": {
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
                "next": "state_a2_3_q3_self_esteem",
            },
            "state_a2_3_q3_self_esteem": {
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
                "next": "state_a2_3_q4_self_esteem",
            },
            "state_a2_3_q4_self_esteem": {
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
                "next": "state_a2_3_q5_self_esteem",
            },
            "state_a2_3_q5_self_esteem": {
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
                "next": "state_a2_3_q6_self_esteem",
            },
            "state_a2_3_q6_self_esteem": {
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
                "next": "state_a2_3_q7_self_esteem",
            },
            "state_a2_3_q7_self_esteem": {
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
                "next": "state_a2_3_q8_self_esteem",
            },
            "state_a2_3_q8_self_esteem": {
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
                "next": "state_a2_3_q9_self_esteem",
            },
            "state_a2_3_q9_self_esteem": {
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
                "next": "state_a2_8_selfesteem_2_worth",
            },
        },
    },
}
