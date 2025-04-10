# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Sexual health literacy
    {
        "start": "endline_8_q1_sexual_health_lit",
        "questions": {
            "endline_8_q1_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Is the following statement true or false?*",
                        "",
                        "People can reduce the risk of getting sexually "
                        "transmitted infections (STIs) by using condoms every "
                        "time they have sex.",
                    ]
                ),
                "options": [
                    ("true", "True"),
                    ("false", "False"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "true": 5,
                    "false": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q2_sexual_health_lit",
            },
            "endline_8_q2_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Is the following statement true or false?*",
                        "",
                        "People can reduce the risk of getting sexually "
                        "transmitted infections (STIs) by only having sex with "
                        "one partner who isn't infected and who has no other partners.",
                    ]
                ),
                "options": [
                    ("true", "True"),
                    ("false", "False"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "true": 5,
                    "false": 1,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q3_sexual_health_lit",
            },
            "endline_8_q3_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How do you feel about the following statements?*",
                        "",
                        "If I'm sexually active, I am able to insist on using "
                        "condoms when I have sex.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                    ("not_sexually_active", "Not sexually active"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 5,
                    "agree": 4,
                    "not_sure": 3,
                    "disagree": 2,
                    "strongly_disagree": 1,
                    "not_sexually_active": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q4_sexual_health_lit",
            },
            "endline_8_q4_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "My sexual needs or desires are important.",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not": 1,
                    "little": 2,
                    "moderately": 3,
                    "very": 4,
                    "extremely": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q5_sexual_health_lit",
            },
            "endline_8_q5_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "I think it would be important to focus on my own pleasure "
                        "as well as my partner's during sexual experiences.",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not": 1,
                    "little": 2,
                    "moderately": 3,
                    "very": 4,
                    "extremely": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q6_sexual_health_lit",
            },
            "endline_8_q6_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "I expect to enjoy sex.",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "not": 1,
                    "little": 2,
                    "moderately": 3,
                    "very": 4,
                    "extremely": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q7_sexual_health_lit",
            },
            "endline_8_q7_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*The last time you had sex, did you or your partner do "
                        "or use something to avoid or delay getting pregnant?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_remember", "I don't remember"),
                    ("havent_had_sex", "I haven't had sex"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "dont_remember": 1,
                    "havent_had_sex": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q8_sexual_health_lit",
            },
            "endline_8_q8_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Did you use a condom last time you had penetrative sex?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("havent_had_sex", "I haven't had sex"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "havent_had_sex": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q9_sexual_health_lit",
            },
            "endline_8_q9_sexual_health_lit": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*What's been the MAIN way you or your partner have "
                        "tried to delay or avoid getting pregnant?*",
                        "",
                        "Please respond with the *number* of an option below",
                    ]
                ),
                "options": [
                    ("pill", "Pill"),
                    ("iud", "IUD (Intra uterine device)"),
                    ("male_condom", "Male condom"),
                    ("female_condom", "Female condom"),
                    ("injection", "Injection"),
                    ("implant", "Implant"),
                    ("diaphragm", "Diaphragm"),
                    ("withdrawal", "Pulling out (withdrawal)"),
                    ("rhythm_method", "Rhythm method"),
                    ("sterilisation", "Sterilisation"),
                    ("breastfeeding", "Breastfeeding"),
                    ("havent_had_sex", "I haven't had sex"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "pill": 5,
                    "iud": 5,
                    "male_condom": 5,
                    "female_condom": 5,
                    "injection": 5,
                    "implant": 5,
                    "diaphragm": 5,
                    "withdrawal": 1,
                    "rhythm_method": 1,
                    "sterilisation": 5,
                    "breastfeeding": 5,
                    "havent_had_sex": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q10A_sexual_health_lit",
            },
            "endline_8_q10A_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How many sexual partners did you have over the last month?*",
                    ]
                ),
                "options": [
                    ("none", "None"),
                    ("one", "One"),
                    ("more_than_one", "More than one"),
                ],
                "scoring": {
                    "none": 5,
                    "one": 5,
                    "more_than_one": 1,
                },
                "next": {
                    "none": "endline_8_q11_sexual_health_lit",
                    "one": "endline_8_q11_sexual_health_lit",
                    "more_than_one": "endline_8_q10B_sexual_health_lit",
                },
            },
            "endline_8_q10B_sexual_health_lit": {
                "type": "text",
                "text": "\n".join(
                    [
                        "*Please tell me how many sexual partners you had in "
                        "the last month.*",
                        "",
                        "Please enter any number e.g. *3*",
                    ]
                ),
                "next": "endline_8_q11_sexual_health_lit",
            },
            "endline_8_q11_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Have you ever been tested for STIs or HIV?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("havent_had_sex", "I haven't had sex"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 1,
                    "havent_had_sex": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_8_q12_sexual_health_lit",
            },
            "endline_8_q12_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Over the past 5 months, do you think that your "
                        "knowledge about the importance of using condoms has "
                        "changed?*",
                    ]
                ),
                "options": [
                    ("yes_improved", "Yes, improved a lot"),
                    ("yes_abit", "Yes, improved a bit "),
                    ("same", "Stayed the same"),
                    ("little_worse", "It’s a little worse"),
                    ("lost_worse", "It’s a lot worse"),
                    ("dont_understand", "I don’t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_8_q13_sexual_health_lit",
            },
            "endline_8_q13_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Which of these has most influenced your knowledge about "
                        "using condoms?*",
                    ]
                ),
                "options": [
                    ("social_media", "Web / social media"),
                    ("bwise_whatsapp", "BWise WhatsApp"),
                    ("bwise_facebook", "BWise facebook page"),
                    ("friends_partner", "Friends / partner"),
                    ("school_university", "School / university"),
                    ("health_facility", "Health facility"),
                    ("tv_radio", "TV / radio"),
                    ("other", "Other"),
                    ("no_change", "No change"),
                ],
                "next": {
                    "other": "endline_8_q13B_sexual_health_lit",
                    "social_media": "endline_8_q14_sexual_health_lit",
                    "bwise_whatsapp": "endline_8_q14_sexual_health_lit",
                    "bwise_facebook": "endline_8_q14_sexual_health_lit",
                    "friends_partner": "endline_8_q14_sexual_health_lit",
                    "school_university": "endline_8_q14_sexual_health_lit",
                    "health_facility": "endline_8_q14_sexual_health_lit",
                    "tv_radio": "endline_8_q14_sexual_health_lit",
                    "no_change": "endline_8_q14_sexual_health_lit",
                },
            },
            "endline_8_q13B_sexual_health_lit": {
                "type": "text",
                "text": "\n".join(
                    [
                        "*Do you mind telling us what has most influenced "
                        "your knowledge of using condoms?*",
                    ]
                ),
                "next": "endline_8_q14_sexual_health_lit",
            },
            "endline_8_q14_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Are you planning to have a child within the next year?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("maybe", "Maybe"),
                    ("no", "No"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_8_q15_sexual_health_lit",
            },
            "endline_8_q15_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you now plan to use condoms more consistently than you "
                        "did 5 months ago?*",
                    ]
                ),
                "options": [
                    ("yes_lot_more", "Yes, a lot more"),
                    ("yes_little_more", "Yes, a little more"),
                    ("no", "No change"),
                    ("no_little_less", "No, a little less"),
                    ("no_lot_less", "No, a lot less"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_8_q16_sexual_health_lit",
            },
            "endline_8_q16_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you now plan to go for STI or HIV tests more often than "
                        "you did 5 months ago?*",
                    ]
                ),
                "options": [
                    ("yes_lot_more", "Yes, a lot more"),
                    ("yes_little_more", "Yes, a little more"),
                    ("no", "No change"),
                    ("no_little_less", "No, a little less"),
                    ("no_lot_less", "No, a lot less"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_8_q17_sexual_health_lit",
            },
            "endline_8_q17_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Which of these has most influenced your plans to use "
                        "condoms or test for STIs/HIV?*",
                    ]
                ),
                "options": [
                    ("social_media", "Web / social media"),
                    ("bwise_whatsapp", "BWise WhatsApp"),
                    ("bwise_facebook", "BWise facebook page"),
                    ("friends_partner", "Friends / partner"),
                    ("school_university", "School / university"),
                    ("health_facility", "Health facility"),
                    ("tv_radio", "TV / radio"),
                    ("other", "Other"),
                    ("no_change", "No change"),
                ],
                "next": {
                    "other": "endline_8_q17B_sexual_health_lit",
                    "social_media": None,
                    "bwise_whatsapp": None,
                    "bwise_facebook": None,
                    "friends_partner": None,
                    "school_university": None,
                    "health_facility": None,
                    "tv_radio": None,
                    "no_change": None,
                },
            },
            "endline_8_q17B_sexual_health_lit": {
                "type": "text",
                "text": "\n".join(
                    [
                        "*Do you mind telling us what has most influenced "
                        "your plans to use condoms or test for STIs/HIV?*",
                    ]
                ),
                "next": None,
            },
        },
    },
}
