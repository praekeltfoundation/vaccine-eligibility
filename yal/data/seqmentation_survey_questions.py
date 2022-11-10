SURVEY_QUESTIONS = {
    "1": {
        "start": "state_s1_4_income",
        "questions": {
            "state_s1_4_income": {
                "text": "How much does everyone in your house make altogether, before "
                "paying for regular monthly items?",
                "options": [
                    ("no_income", "No income"),
                    ("R1-R400", "R1 - R400"),
                    ("R401-R800", "R401 - R800"),
                    ("R801-R1600", "R801 - R1 600"),
                    ("R1601-R3200", "R1 601 - R3 200"),
                    ("R3201-R6400", "R3 201 - R6 400"),
                    ("R6401-R12800", "R6 401 - R12 800"),
                    ("R12801-R25600", "R12 801 - R25 600"),
                    ("R25601-R51200", "R25 601 - R51 200"),
                    ("R51201-R102400", "R51 201 - R102 400"),
                    ("R102401-R204800", "R102 401 - R204 800"),
                    ("R204801+", "R204 801 or more"),
                ],
                "next": "state_relationship_status",
            },
            "state_relationship_status": {
                "text": "What is your present relationship status?",
                "options": [
                    ("no", "Not currently dating"),
                    ("serious", "In a serious relationship"),
                    ("not_serious", "In a relationship, but not a serious one"),
                ],
                "next": "state_s1_6_detail_monthly_sex_partners",
            },
            "state_s1_6_detail_monthly_sex_partners": {
                "text": "\n".join(
                    [
                        "*Ok. You can tell me how many sexual partners you had here.*",
                        "",
                        "_Just type and send_",
                    ]
                ),
                "next": None,
            },
        },
    },
    "2": {
        "start": "state_s2_1_knowledge_1",
        "questions": {
            "state_s2_1_knowledge_1": {
                "text": "\n".join(
                    [
                        "Do you think this is True or False?_",
                        "",
                        "*People can reduce the risk of getting STIs by using condoms "
                        "every time they have sexual intercourse.*",
                    ]
                ),
                "options": ["True", "False"],
                "next": "state_s2_2_knowledge_2",
            },
            "state_s2_2_knowledge_2": {
                "text": "_Do you think this is True or False?_ \n\n*People can reduce "
                "the risk of getting STIs by limiting sexual intercourse to one "
                "partner who is not infected and has no other partners.*",
                "options": ["True", "False"],
                "next": None,
            },
        },
    },
    "3": {
        "start": "state_s3_1_loc_1_boss",
        "questions": {
            "state_s3_1_loc_1_boss": {
                "text": "_The following statements may apply more or less to you. To "
                "what extent do you think each statement applies to you personally?_ "
                "\n\n*I’m my own boss.*",
                "options": [
                    "Does not apply at all",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                ],
                "next": "state_s3_2_loc_2_work",
            },
            "state_s3_2_loc_2_work": {
                "text": "_The following statements may apply more or less to you. To "
                "what extent do you think each statement applies to you personally?_ "
                "\n\n*If I work hard, I will success.*",
                "options": [
                    "Does not apply at all",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                ],
                "next": None,
            },
        },
    },
}
