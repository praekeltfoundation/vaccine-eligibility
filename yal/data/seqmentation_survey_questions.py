SURVEY_QUESTIONS = {
    "1": {
        "start": "state_s1_1_gender",
        "questions": {
            "state_s1_1_gender": {
                "text": "*What gender do you identity with?*",
                "options": [
                    ("female", "Female"),
                    ("male", "Male"),
                    ("non_binary", "Non-binary"),
                    ("trans", "Transgender"),
                    ("self_describe", "Self-describe"),
                    ("prefer_not_disclose", "Prefer not to disclose"),
                ],
                "next": {
                    "female": "state_s1_3_age",
                    "male": "state_s1_2_sex_with_men",
                    "non_binary": "state_s1_2_sex_with_men",
                    "trans": "state_s1_2_sex_with_men",
                    "self_describe": "state_s1_2_sex_with_men",
                    "prefer_not_disclose": "state_s1_2_sex_with_men",
                },
            },
            "state_s1_2_sex_with_men": {
                "text": "*Do you sometimes, or have you previously had sex with men?*",
                "options": ["Yes", "No"],
                "next": "state_s1_3_age",
            },
            "state_s1_3_age": {
                "text": "*How old are you?*\n\n_Reply with your age e.g. 23_",
                "type": "freetext",
                "next": "state_s1_4_income",
            },
            "state_s1_4_income": {
                "text": "*How much does everyone in your house make altogether, before "
                "paying for regular monthly items?*",
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
            "state_s1_5_relationship_status": {
                "text": "*What is your present relationship status?*",
                "options": [
                    ("no", "Not currently dating"),
                    ("serious", "In a serious relationship"),
                    ("not_serious", "In a relationship, but not a serious one"),
                ],
                "next": "state_s1_6_monthly_sex_partners",
            },
            "state_s1_6_monthly_sex_partners": {
                "text": "*How many sexual partners did you have over the last month?*",
                "options": [
                    ("1-2", "One - two"),
                    ("2-3", "Two - three"),
                    ("other", "Other"),
                    ("skip", "Skip"),
                ],
                "next": {
                    "1-2": "state_s1_7_condom",
                    "2-3": "state_s1_7_condom",
                    "other": "state_s1_6_detail_monthly_sex_partners",
                    "skip": "state_s1_7_condom",
                },
            },
            "state_s1_6_detail_monthly_sex_partners": {
                "type": "freetext",
                "text": "\n".join(
                    [
                        "*Ok. You can tell me how many sexual partners you had here.*",
                        "",
                        "_Just type and send_",
                    ]
                ),
                "next": "state_s1_7_condom",
            },
            "state_s1_7_condom": {
                "text": "*Did you use a condom last time you had penetrative sex?*",
                "options": ["Yes", "No", "Skip"],
                "next": "state_s1_8_sti_tested",
            },
            "state_s1_8_sti_tested": {
                "text": "*Have you ever been tested for STIs and HIV?*",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": {
                    "yes": "state_s1_9_detail_sti_tested",
                    "no": "state_sti_tested_skip_msg",
                },
            },
            "state_sti_tested_skip_msg": {
                "type": "info",
                "text": "Please note, because you've selected NO, we're skipping some "
                "questions as they don't apply to you.",
                "next": "state_s1_12_5_partners_stis",
            },
            "state_s1_9_detail_sti_tested": {
                "text": "*What STIs have you been tested for?*",
                "options": [
                    ("reply_with_sti", "Reply with STI"),
                    ("skip", "Skip"),
                ],
                "next": {
                    "reply_with_sti": "state_s1_9_detail_sti_name",
                    "skip": "state_s1_10_tested_positive",
                },
            },
            "state_s1_9_detail_sti_name": {
                "type": "freetext",
                "text": "\n".join(
                    [
                        "*Ok. You can tell me STI you were tested for here.*",
                        "",
                        "_Just type and send_",
                    ]
                ),
                "next": "state_s1_10_tested_positive",
            },
            "state_s1_10_tested_positive": {
                "text": "*Were you diagnosed with an STI in the past?*",
                "options": ["Yes", "No", "Skip"],
                "next": "state_s1_11_hiv_status",
            },
            "state_s1_11_hiv_status": {
                "text": "*Are you HIV positive?*",
                "options": [("yes", "Yes"), ("no", "No"), ("skip", "Skip")],
                "next": {
                    "yes": "state_s1_12_hiv_medication",
                    "no": "state_s1_12_5_partners_stis",
                    "skip": "state_s1_12_5_partners_stis",
                },
            },
            "state_s1_12_hiv_medication": {
                "text": "Do you take your medication (PREP or ART) on a regular basis?",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": "state_s1_12_5_partners_stis",
            },
            "state_s1_12_5_partners_stis": {
                "text": "*Do you know if any of your sexual partners have had an STI?*",
                "options": ["Yes", "No", "Skip"],
                "next": "state_s1_13_addition_1_cut_down",
            },
            "state_s1_13_addition_1_cut_down": {
                "text": "*Have you ever felt you needed to cut down on your drinking "
                "or drug use?*",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": "state_s1_13_addition_2_criticise",
            },
            "state_s1_14_addition_2_criticise": {
                "text": "*Have people annoyed you by criticising your drinking or drug "
                "use?*",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": "state_s1_15_addition_3_guilt",
            },
            "state_s1_15_addition_3_guilt": {
                "text": "*Have you ever felt guilty about drinking or drug use?*",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": "state_s1_16_addition_4_morning",
            },
            "state_s1_16_addition_4_morning": {
                "text": "*Have you ever felt you needed a drink or used drugs first "
                "thing in the morning (eye‐opener) to steady your nerves or to get rid "
                "of a hangover?*",
                "options": [("yes", "Yes"), ("no", "No")],
                "next": "state_s1_17_sexuality",
            },
            "state_s1_17_sexuality": {
                "text": "*What is your sexual orientation?*",
                "options": [
                    ("straight", "Straight"),
                    ("gay_or_lesbian", "Gay or Lesbian"),
                    ("bisexual", "Bisexual"),
                    ("queer", "Queer"),
                    ("asexual", "Asexual"),
                    ("self_describe", "Prefer to self-describe"),
                    ("not_say", "Prefer not to say"),
                ],
                "next": "state_s1_18_disability_1_vision",
            },
            "state_s1_18_disability_1_vision": {
                "text": "*Do you have difficulty seeing, even if wearing glasses?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_19_disability_2_hearing",
            },
            "state_s1_19_disability_2_hearing": {
                "text": "*Do you have difficulty hearing, even if using a hearing "
                "aid(s)?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_20_disability_3_walking",
            },
            "state_s1_20_disability_3_walking": {
                "text": "*Do you have difficulty walking or climbing steps?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_21_disability_4_concentrate",
            },
            "state_s1_21_disability_4_concentrate": {
                "text": "*Do you have difficulty remembering or concentrating?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_22_disability_5_selfcare",
            },
            "state_s1_22_disability_5_selfcare": {
                "text": "*Do you have difficulty taking care of yourself, like washing "
                "all over or getting dressing?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_23_disability_6_communicate",
            },
            "state_s1_23_disability_6_communicate": {
                "text": "*Do you have difficulty communicating in your home language, "
                "like being understood or understanding others for example?*",
                "options": [
                    ("no", "No difficulty"),
                    ("some", "Some difficulty"),
                    ("alot", "A lot of difficulty"),
                    ("cannot_at_all", "Cannot do at all"),
                ],
                "next": "state_s1_progress_complete",
            },
            "state_s1_progress_complete": {
                "type": "info",
                "text": "\n".join(
                    [
                        "😎 *YOU'RE DOING REALLY WELL.*",
                        "",
                        "Section 1 complete, your airtime is getting closer. *Let's "
                        "move onto section 2!* ➡️",
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
                        "_Do you think this is True or False?_",
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
                "next": "state_s2_progress_complete",
            },
            "state_s2_progress_complete": {
                "type": "info",
                "text": "\n".join(
                    [
                        "😎 *CONGRATS. YOU'RE HALFWAY THERE!*",
                        "",
                        "Section 2 complete, keep going. *Let's move onto section 3!* "
                        "👍🏾",
                    ]
                ),
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
