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
        "start": "state_s2_1_knowledge_1_condoms",
        "questions": {
            "state_s2_1_knowledge_1_condoms": {
                "text": "\n".join(
                    [
                        "_Do you think this is True or False?_",
                        "",
                        "*People can reduce the risk of getting STIs by using condoms "
                        "every time they have sexual intercourse.*",
                    ]
                ),
                "options": ["True", "False"],
                "next": "state_s2_2_knowledge_2_exclusivity",
            },
            "state_s2_2_knowledge_2_exclusivity": {
                "text": "\n".join(
                    [
                        "_Do you think this is True or False?_",
                        "",
                        "*People can reduce the risk of getting STIs by limiting "
                        "sexual intercourse to one partner who is not infected and "
                        "has no other partners.*",
                    ]
                ),
                "options": ["True", "False"],
                "next": "state_s2_3_knowledge_3_condoms_exclusivity",
            },
            "state_s2_3_knowledge_3_condoms_exclusivity": {
                "text": "\n".join(
                    [
                        "_Do you think this is True or False?_",
                        "",
                        "*People can reduce the risk of getting STIs by using condoms "
                        "every time they have sexual intercourse and by limiting "
                        "sexual intercourse to one partner who is not infected and "
                        "has no other partners.*",
                    ]
                ),
                "options": ["True", "False"],
                "next": "state_s2_4_competence_1_consent",
            },
            "state_s2_4_competence_1_consent": {
                "text": "If Teddy goes out to a restaurant and starts a conversation "
                "with someone he is sexually attracted to, *what is most important "
                "way that Teddy can decide if the person he is talking to wants to "
                "have sex with him?*",
                "options": [
                    ("look", "By the way they are looking at him"),
                    ("clothes", "By what they are wearing"),
                    ("carry_condoms", "If they carry condoms"),
                    ("previous_sex", "If Teddy has had sex with them before"),
                    ("verbal_consent", "If they verbally consent to have sex"),
                    ("dont_know", "I don't know"),
                ],
                "next": "state_s2_5_competence_2_right_to_sex",
            },
            "state_s2_5_competence_2_right_to_sex": {
                "text": "\n".join(
                    [
                        "Robert and Samantha have been dating for 5 years and love "
                        "each other very much. Every year on Robert's birthday, "
                        "Samantha promises him sex for his birthday. This year, "
                        "Samantha tells Robert that she is too tired for sex.",
                        "",
                        "To what extent do you agree with this statement: *Robert has "
                        "the right to force Samantha to have sex.*",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                ],
                "next": "state_s2_6_competence_3_insist_condoms",
            },
            "state_s2_6_competence_3_insist_condoms": {
                "text": "\n".join(
                    [
                        "How much do you agree with the following statement:",
                        "",
                        "*If sexually active, I am able to insist on condom use when "
                        "I have sex.*",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                    ("not_active", "I am not sexually active"),
                ],
                "next": "state_s2_7_competence_4_saying_no",
            },
            "state_s2_7_competence_4_saying_no": {
                "text": "*If you are in a relationship, which statement describes you "
                "best?*",
                "options": [
                    (
                        "comfortable",
                        "I feel comfortable telling my partner no if they want to "
                        "have sex, but I do not want to",
                    ),
                    (
                        "difficult",
                        "I find it difficult to tell my partner 'no' if they want to "
                        "have sex but I do not want to",
                    ),
                    ("not_sure", "I am not sure"),
                    ("not_in_relationship", "Not in a relationship"),
                ],
                "next": "state_s2_8_enjoyment_1_needs_important",
            },
            "state_s2_8_enjoyment_1_needs_important": {
                "text": "*My sexual needs or desires are important.*",
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Moderately true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                ],
                "next": "state_s2_9_enjoyment_2_own_pleasure",
            },
            "state_s2_9_enjoyment_2_own_pleasure": {
                "text": "*I think it would be important to focus on my own pleasure "
                "as well as my partner's during sexual experiences.*",
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Moderately true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                ],
                "next": "state_s2_10_enjoyment_3_expect_enjoy",
            },
            "state_s2_10_enjoyment_3_expect_enjoy": {
                "text": "*I expect to enjoy sex*",
                "options": ["TODO"],
                "next": "TODO",
            },
            "state_s2_11_contraceptive_1_use": {
                "text": "*During the last time you had sex, did you or your partner "
                "do something or use any method to avoid or delay getting pregnant?*",
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_remember", "Don’t remember"),
                    ("havent_had_sex", "I haven't had sex"),
                ],
                "next": "state_s2_12_contraceptive_2_detail",
            },
            "state_s2_12_contraceptive_2_detail": {
                "text": "*What has been the main method that you or your partner "
                "have used to delay or avoid getting pregnant?*",
                "options": [
                    ("none", "None"),
                    ("pill", "Pill"),
                    ("iud", "Intra uterine device (IUD)"),
                    ("male_condom", "Male condom"),
                    ("female_condom", "Female condom"),
                    ("inject", "Injectables"),
                    ("implant", "Implants"),
                    ("diaphragm", "Diaphragm"),
                    ("foam_jelly", "Foam/jelly"),
                    ("lactational", "Lactational amenorrhea method"),
                    ("cyclebeads", "Standard days method / cyclebeads"),
                    ("female_sterilisation", "Female sterilisation"),
                    ("male_sterilisation", "Male sterilisation"),
                    ("breastfeeding", "Exclusive breastfeeding"),
                    ("havent_had_sex", "I haven't had sex"),
                ],
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
                "text": "\n".join(
                    [
                        "_The following statements may apply more or less to you. To "
                        "what extent do you think each statement applies to you "
                        "personally?_",
                        "",
                        "*I’m my own boss.*",
                    ]
                ),
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
                "text": "\n".join(
                    [
                        "_The following statements may apply more or less to you. To "
                        "what extent do you think each statement applies to you "
                        "personally?_",
                        "",
                        "*If I work hard, I will success.*",
                    ]
                ),
                "options": [
                    "Does not apply at all",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                ],
                "next": "state_s3_3_loc_3_others",
            },
            "state_s3_3_loc_3_others": {
                "text": "\n".join(
                    [
                        "_The following statements may apply more or less to you. To "
                        "what extent do you think each statement applies to you "
                        "personally?_",
                        "",
                        "*What I do is mainly determined by others.*",
                    ]
                ),
                "options": [
                    "Does not apply at all",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                ],
                "next": "state_s3_4_loc_4_fate",
            },
            "state_s3_4_loc_4_fate": {
                "text": "\n".join(
                    [
                        "_The following statements may apply more or less to you. To "
                        "what extent do you think each statement applies to you "
                        "personally?_",
                        "",
                        "*Fate often gets in the way of my plans.*",
                    ]
                ),
                "options": [
                    "Does not apply at all",
                    "Applies somewhat",
                    "Applies",
                    "Applies a lot",
                    "Applies completely",
                ],
                "next": "state_s3_5_spch_doing",
            },
            "state_s3_5_spch_doing": {
                "text": "*How good a job do you feel you are doing in taking care of "
                "your health?*",
                "options": [
                    "Excellent",
                    "Very Good",
                    "Good",
                    "Fair",
                    "Poor",
                ],
                "next": "state_s3_6_spch_clinic",
            },
            "state_s3_6_spch_clinic": {
                "text": "*When I have a health need (e.g. contraception, flu "
                "symptoms), I go to my closest clinic.*",
                "options": [
                    "Yes",
                    "No",
                    "Sometimes",
                ],
                "next": "state_s3_7_selfesteem_1_qualities",
            },
            "state_s3_7_selfesteem_1_qualities": {
                "text": "*I feel that I am a person of worth, at least on an equal "
                "plane with others.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_8_selfesteem_2_worth",
            },
            "state_s3_8_selfesteem_2_worth": {
                "text": "*I feel that I am a person of worth, at least on an equal "
                "plane with others.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_9_selfesteem_3_failure",
            },
            "state_s3_9_selfesteem_3_failure": {
                "text": "*All in all, I am inclined to feel that I am a failure.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_10_selfesteem_4_capable",
            },
            "state_s3_10_selfesteem_4_capable": {
                "text": "*I am able to do things as well as most other people.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_11_selfesteem_5_proud",
            },
            "state_s3_11_selfesteem_5_proud": {
                "text": "*I feel I do not have much to be proud of.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_12_selfesteem_6_positive",
            },
            "state_s3_12_selfesteem_6_positive": {
                "text": "*I take a positive attitude toward myself.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_13_self_esteem_7_satisfied",
            },
            "state_s3_13_self_esteem_7_satisfied": {
                "text": "*On the whole, I am satisfied with myself.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_14_selfesteem_8_respect",
            },
            "state_s3_14_selfesteem_8_respect": {
                "text": "*I wish I could have more respect for myself.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_15_selfesteem_9_nogood",
            },
            "state_s3_15_selfesteem_9_nogood": {
                "text": "*At times I think I am no good at all.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_16_selfesteem_10_useless",
            },
            "state_s3_16_selfesteem_10_useless": {
                "text": "*I certainly feel useless at times.*",
                "options": [
                    "Strongly agree",
                    "Agree",
                    "Disagree",
                    "Strongly disagree",
                ],
                "next": "state_s3_17_resilience_1_believe",
            },
            "state_s3_17_resilience_1_believe": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I believe in myself*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_18_resilience_2_adapt",
            },
            "state_s3_18_resilience_2_adapt": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I can adapt to challenging situations*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_19_resilience_3_solutions",
            },
            "state_s3_19_resilience_3_solutions": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I find solutions to problems I encounter*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_20_resilience_4_difficulties",
            },
            "state_s3_20_resilience_4_difficulties": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I can keep going despite difficulties*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_21_resilience_5_cope",
            },
            "state_s3_21_resilience_5_cope": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I can cope with competing demands (for my time or "
                        "attention)*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_22_resilience_6_hope",
            },
            "state_s3_22_resilience_6_hope": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*Even when there are setbacks or obstacles, I am hopeful "
                        "about my future*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_23_resilience_7_emotions",
            },
            "state_s3_23_resilience_7_emotions": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I am generally in control of my emotions*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_28_resilience_8_pride",
            },
            "state_s3_24_resilience_8_pride": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I take pride in things I have achieved*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_25_resilience_9_rise",
            },
            "state_s3_25_resilience_9_rise": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*When faced with difficulties, I rise to the challenge*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_26_resilience_10_meaning",
            },
            "state_s3_26_resilience_10_meaning": {
                "text": "\n".join(
                    [
                        "_Do you agree with the following statements?_",
                        "",
                        "*I can find meaning in my life*",
                    ]
                ),
                "options": [
                    "Not at all",
                    "A little",
                    "Somewhat",
                    "Quite a bit",
                    "A lot",
                ],
                "next": "state_s3_27_gen_att_1_beating",
            },
            "state_s3_27_gen_att_1_beating": {
                "text": "\n".join(
                    [
                        "_How do you feel about each statement? There are no right or "
                        "wrong answers._",
                        "",
                        "*There are times when a woman deserves to be beaten*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Somewhat agree",
                    "Do not agree",
                ],
                "next": "state_s3_28_gen_att_2_pregnant",
            },
            "state_s3_28_gen_att_2_pregnant": {
                "text": "\n".join(
                    [
                        "_How do you feel about each statement? There are no right or "
                        "wrong answers._",
                        "",
                        "*It’s a woman’s responsibility to avoid getting pregnant*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Somewhat agree",
                    "Do not agree",
                ],
                "next": "state_s3_29_gen_att_3_contraception",
            },
            "state_s3_29_gen_att_3_contraception": {
                "text": "\n".join(
                    [
                        "_How do you feel about each statement? There are no right or "
                        "wrong answers._",
                        "",
                        "*A man and a woman should decide together what type of "
                        "contraceptive to use*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Somewhat agree",
                    "Do not agree",
                ],
                "next": "state_s3_30_gen_att_4_parenting",
            },
            "state_s3_30_gen_att_4_parenting": {
                "text": "\n".join(
                    [
                        "_How do you feel about each statement? There are no right or "
                        "wrong answers._",
                        "",
                        "*If a guy gets women pregnant, the child is both of their "
                        "responsibility*",
                    ]
                ),
                "options": [
                    "Strongly agree",
                    "Somewhat agree",
                    "Do not agree",
                ],
                "next": "state_s3_progress_complete",
            },
            "state_s3_progress_complete": {
                "type": "info",
                "text": "\n".join(
                    [
                        "🤩 *SHO! That was a long one but guess what, YOU'RE ALMOST "
                        "DONE!*",
                        "",
                        "Section 3 complete. *Just one more section* to go and your "
                        "airtime will be in you phone.📲",
                    ]
                ),
                "next": None,
            },
        },
    },
    "4": {
        "start": "state_s4_start",
        "questions": {
            "state_s4_start": {
                "type": "info",
                "text": "\n".join(
                    [
                        "*BWise / Survey*",
                        "*-----*",
                        "",
                        "Over the last two weeks, how often have you been bothered by "
                        "the following problems?",
                    ]
                ),
                "next": "state_s4_1_depression_1_anxious",
            },
            "state_s4_1_depression_1_anxious": {
                "text": "*Feeling nervous, anxious or on edge*",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_s4_2_depression_2_worrying",
            },
            "state_s4_2_depression_2_worrying": {
                "text": "*Not being able to stop or control worrying*",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_s4_3_depression_3_hopeless",
            },
            "state_s4_4_depression_4_interest": {
                "text": "*Little interest or pleasure in doing things*",
                "options": [
                    "Not at all",
                    "Several days",
                    "More than half the days",
                    "Nearly every day",
                ],
                "next": "state_s4_5_connectedness",
            },
            "state_s4_5_connectedness": {
                "text": "*Do you have someone to talk to when you have a worry or "
                "problem?*",
                "options": [
                    "Never",
                    "Some of the time",
                    "Most of the time",
                    "All the time",
                ],
                "next": "state_s4_6_self_concept_1_myself",
            },
            "state_s4_6_self_concept_1_myself": {
                "text": "\n".join(
                    [
                        "_How do you feel about this statement?_",
                        "",
                        "*I feel good about myself*",
                    ]
                ),
                "options": [
                    "Never",
                    "Some of the time",
                    "Most of the time",
                    "All the time",
                ],
                "next": "state_s4_7_self_concept_2_body",
            },
            "state_s4_7_self_concept_2_body": {
                "text": "\n".join(
                    [
                        "_How do you feel about this statement?_",
                        "",
                        "*I feel good about my body*",
                    ]
                ),
                "options": [
                    "Never",
                    "Some of the time",
                    "Most of the time",
                    "All the time",
                ],
                "next": None,
            },
        },
    },
}
