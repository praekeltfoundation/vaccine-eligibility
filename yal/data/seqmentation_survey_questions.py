SURVEY_QUESTIONS = {
    "1": {
        "start": "state_s1_4_income",
        "questions": {
            "state_s1_4_income": {
                "text": "How much does everyone in your house make altogether, before "
                "paying for regular monthly items?",
                "options": [
                    "No income",
                    "R1 - R400",
                    "R401 - R800",
                    "R801 - R1 600",
                    "R1 601 - R3 200",
                    "R3 201 - R6 400",
                ],
                "next": "state_relationship_status",
            },
            "state_relationship_status": {
                "text": "What is your present relationship status?",
                "options": [
                    "Not currently dating",
                    "In a serious relationship",
                    "In a relationship, but not a serious one",
                ],
                "next": None,
            },
        },
    },
    "2": {
        "start": "state_s2_1_knowledge_1",
        "questions": {
            "state_s2_1_knowledge_1": {
                "text": "_Do you think this is True or False?_ \n\n*People can reduce "
                "the risk of getting STIs by using condoms every time they have "
                "sexual intercourse.*",
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
