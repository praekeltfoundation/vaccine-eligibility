# Assessment state naming convention
# state_a[number]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Sexual health literacy
    {
        "start": "state_a1_q1_sexual_health_lit",
        "questions": {
            "state_a1_q1_sexual_health_lit": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*_People can reduce the risk of getting STIs by:_*",
                        "",
                        "[persona_emoji] _Reply with the *number* "
                        "of your chosen answer:_",
                    ]
                ),
                "options": [
                    (
                        "condoms",
                        "using condoms every time they have sexual intercourse.",
                    ),
                    (
                        "single_partner",
                        "only having sex with one partner who isn't infected and who "
                        "has no other partners.",
                    ),
                ],
                "scoring": {"condoms": 5, "single_partner": 0},
                "next": "state_a1_q2_sexual_health_lit",
            },
            "state_a1_q2_sexual_health_lit": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "_*If Teddy goes out to a restaurant and starts chatting "
                        "with someone he is sexually attracted to, what is most "
                        "appropriate way Teddy can tell that person wants to "
                        "have sex with him?*_",
                        "",
                        "[persona_emoji] _Reply with the *number* "
                        "of your chosen answer:_",
                    ]
                ),
                "options": [
                    ("looking", "By the way they are looking at him"),
                    ("wearing", "By what they are wearing"),
                    ("condoms", "If they carry condoms"),
                    ("previous_sex", "If Teddy has had sex with them before"),
                    ("verbal_consent", "If they verbally consent to have sex"),
                    ("dont_know", "I don't know"),
                ],
                "scoring": {
                    "looking": 0,
                    "wearing": 0,
                    "condoms": 0,
                    "previous_sex": 0,
                    "verbal_consent": 5,
                    "dont_know": 0,
                },
                "next": "state_a1_q3_sexual_health_lit_info",
            },
            "state_a1_q3_sexual_health_lit_info": {
                "type": "info",
                "text": "\n".join(
                    [
                        "_*Robert and Samantha have been dating for 5 years and love "
                        "each other very much.*_",
                        "",
                        "_*Every year on Robert's birthday, "
                        "Samantha promises him sex for his birthday. This year, "
                        "Samantha tells Robert that she is too tired for sex.*_",
                    ]
                ),
                "next": "state_a1_q3_sexual_health_lit",
            },
            "state_a1_q3_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*_How much do you agree or disagree with this statement?_* 👇🏾",
                        "",
                        "Robert has the right to force Samantha to have sex.",
                        "",
                        "[persona_emoji] _*Tap the button* below and select the option "
                        "that describes how you feel._",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                ],
                "scoring": {
                    "strongly_agree": 5,
                    "agree": 3,
                    "not_sure": 2,
                    "disagree": 1,
                    "strongly_disagree": 0,
                },
                "next": "state_a1_q4_sexual_health_lit",
            },
            "state_a1_q4_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How much do you agree or disagree with "
                        "the following statement:*",
                        "",
                        "If sexually active, I _am_ able to insist on condoms when "
                        "I have sex.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                    ("not_active", "Not sexually active"),
                ],
                "scoring": {
                    "strongly_agree": 5,
                    "agree": 3,
                    "not_sure": 2,
                    "disagree": 0,
                    "strongly_disagree": 0,
                },
                "next": "state_a1_q5_sexual_health_lit",
            },
            "state_a1_q5_sexual_health_lit": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*If you are in a relationship, which of these statements "
                        "describes you best?*",
                        "",
                        "[persona_emoji] _Reply with the *number* "
                        "of your chosen answer:_",
                        "",
                    ]
                ),
                "options": [
                    (
                        "easy",
                        "I'm cool with telling bae no if they want to have sex but I "
                        "don't.",
                    ),
                    (
                        "difficult",
                        "I find it hard to say no to bae if bae wants to have sex but "
                        "I don't.",
                    ),
                    (
                        "not_sure",
                        "I'm not sure how I feel about saying no when bae wants to "
                        "have sex and I don't.",
                    ),
                    ("no_relationship", "I'm not in a relationship"),
                ],
                "scoring": {
                    "easy": 5,
                    "difficult": 0,
                    "not_sure": 1,
                    "no_relationship": 0,
                },
                "next": "state_a1_q6_sexual_health_lit",
            },
            "state_a1_q6_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*How true does this statement sound to you?*_",
                        "",
                        "My sexual needs or desires are important.",
                        "",
                        "[persona_emoji] _*Tap the button* below and "
                        "select the option that describes how you feel_",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                ],
                "scoring": {
                    "not": 0,
                    "little": 0,
                    "moderately": 0,
                    "very": 3,
                    "extremely": 5,
                },
                "next": "state_a1_q7_sexual_health_lit",
            },
            "state_a1_q7_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*How true does this statement sound to you?*_",
                        "",
                        "I think it would be important to focus on my own "
                        "pleasure as well as my partner's during sexual experiences.",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                ],
                "scoring": {
                    "not": 0,
                    "little": 0,
                    "moderately": 0,
                    "very": 3,
                    "extremely": 5,
                },
                "next": "state_a1_q8_sexual_health_lit",
            },
            "state_a1_q8_sexual_health_lit": {
                "type": "list",
                "text": "\n".join(
                    [
                        "_*How true does this statement sound to you?*_",
                        "",
                        "I expect to enjoy sex.",
                    ]
                ),
                "options": [
                    ("not", "Not at all true"),
                    ("little", "A little true"),
                    ("moderately", "Kind of true"),
                    ("very", "Very true"),
                    ("extremely", "Extremely true"),
                ],
                "scoring": {
                    "not": 0,
                    "little": 0,
                    "moderately": 0,
                    "very": 3,
                    "extremely": 5,
                },
                "next": "state_a1_q9A_sexual_health_lit",
            },
            "state_a1_q9A_sexual_health_lit": {
                "text": "*The last time you had sex, did you or your partner "
                "do something or use any method to avoid or delay getting pregnant?*",
                "type": "choice",
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("forgot", "Don't remember"),
                    ("virgin", "Haven't had sex"),
                ],
                "scoring": {
                    "yes": 5,
                    "no": 0,
                    "forgot": 0,
                    "virgin": 3,
                },
                "next": {
                    "yes": "state_a1_q9B_sexual_health_lit",
                    "no": None,
                    "forgot": None,
                    "virgin": None,
                },
            },
            "state_a1_q9B_sexual_health_lit": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*What's been the MAIN way you or your partner "
                        "have tried to delay or avoid getting pregnant?*",
                        "",
                        "_Reply with the *number* of one of the options below._",
                    ]
                ),
                "options": [
                    ("pill", "Pill"),
                    ("iud", "Intra uterine device (IUD)"),
                    ("male_condom", "Male condom"),
                    ("female_condom", "Female condom"),
                    ("injectable", "Injectables"),
                    ("implant", "Implants"),
                    ("diaphragm", "Diaphragm"),
                    ("foam_jelly", "Foam/jelly"),
                    ("withdrawal", "Pulling out (withdrawal method)"),
                    ("lactational_amenorrhea", "Lactational amenorrhea method"),
                    ("standard_days", "Standard days method"),
                    ("cyclebeads", "Cyclebeads"),
                    ("female_sterilisation", "Female sterilisation"),
                    ("male_sterilisation", "Male sterilisation"),
                    ("exclusive_breastfeeding", "Exclusive breastfeeding"),
                ],
                "scoring": {
                    "pill": 5,
                    "iud": 5,
                    "male_condom": 3,
                    "female_condom": 3,
                    "injectable": 4,
                    "implant": 4,
                    "diaphragm": 2,
                    "foam_jelly": 1,
                    "withdrawal": 0,
                    "lactational_amenorrhea": 2,
                    "standard_days": 0,
                    "cyclebeads": 1,
                    "female_sterilisation": 2,
                    "male_sterilisation": 2,
                    "exclusive_breastfeeding": 1,
                },
                "next": None,
            },
        },
    },
}
