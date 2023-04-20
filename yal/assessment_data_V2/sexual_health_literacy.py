# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Sexual health literacy
    {
        "start": "baseline_7_q1_sexual_health_lit",
        "questions": {
            "baseline_7_q1_sexual_health_lit": {
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
                "next": "baseline_7_q2_sexual_health_lit",
            },
            "baseline_7_q2_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Is the following statement true or false?*",
                        "",
                        "People can reduce the risk of getting sexual STIs by only "
                        "having sex with one partner who isn't infected and who has no "
                        "other partners.",
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
                "next": "baseline_7_q3_sexual_health_lit",
            },
            "baseline_7_q3_sexual_health_lit": {
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
                "next": "baseline_7_q4_sexual_health_lit",
            },
            "baseline_7_q4_sexual_health_lit": {
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
                "next": "baseline_7_q5_sexual_health_lit",
            },
            "baseline_7_q5_sexual_health_lit": {
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
                "next": "baseline_7_q6_sexual_health_lit",
            },
            "baseline_7_q6_sexual_health_lit": {
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
                "next": "baseline_7_q7_sexual_health_lit",
            },
            "baseline_7_q7_sexual_health_lit": {
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
                "next": "baseline_7_q8_sexual_health_lit",
            },
            "baseline_7_q8_sexual_health_lit": {
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
                "next": "baseline_7_q9_sexual_health_lit",
            },
            "baseline_7_q9_sexual_health_lit": {
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
                "next": "baseline_7_q10A_sexual_health_lit",
            },
            "baseline_7_q10A_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How many sexual partners did you have over the last "
                        "month?*",
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
                    "none": "baseline_7_q11_sexual_health_lit",
                    "one": "baseline_7_q11_sexual_health_lit",
                    "more_than_one": "baseline_7_q10B_sexual_health_lit",
                },
            },
            "baseline_7_q10B_sexual_health_lit": {
                "type": "text",
                "text": "\n".join(
                    [
                        "*Please tell me how many sexual partners you had in "
                        "the last month.*",
                        "",
                        "Please enter any number e.g. *3*",
                    ]
                ),
                "next": "baseline_7_q11_sexual_health_lit",
            },
            "baseline_7_q11_sexual_health_lit": {
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
                "next": "baseline_7_q12_sexual_health_lit",
            },
            "baseline_7_q12_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Remember*- your answers are not linked back to you or "
                        "shared with anyone."
                        "",
                        "*Are you currently living with HIV?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("skip_question", "Skip question"),
                ],
                "next": {
                    "yes": "baseline_7_q13_sexual_health_lit",
                    "no": "baseline_7_q14_sexual_health_lit",
                    "skip_question": None,
                },
            },
            "baseline_7_q13_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you take ART (antiretroviral therapy) medication "
                        "on a regular basis?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("skip_question", "Skip question"),
                ],
                "next": {
                    "yes": None,
                    "no": None,
                    "skip_question": None,
                },
            },
            "baseline_7_q14_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you take PrEP (Pre-exposure prophylaxis) "
                        "medication on a regular basis?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("skip_question", "Skip question"),
                ],
                "next": None,
            },
        },
    },
}
