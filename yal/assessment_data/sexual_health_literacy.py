ASSESSMENT_QUESTIONS = {
    "1": {
        "start": "state_s1_1_sex_health_lit_sti",
        "questions": {
            "state_s1_1_sex_health_lit_sti": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*_People can reduce the risk of getting STIs by:_*",
                        "",
                        "[persona_emoji] _Reply with the *number* "
                        "of your chosen answer:_",
                        "",
                    ]
                ),
                "options": [
                    (
                        "condoms",
                        "using to condoms every time they have sexual intercourse.",
                    ),
                    (
                        "single_partner",
                        "only having sex with one partner who isn't infected and who "
                        "has no other partners.",
                    ),
                ],
                "next": "state_s1_2_sex_health_lit_consent",
            },
            "state_s1_2_sex_health_lit_consent": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*If Teddy goes out to a restaurant and starts chatting "
                        "with someone he is sexually attracted to, what is most "
                        "appropriate way Teddy can tell that person wants to "
                        "have sex with him?*",
                        "",
                        "[persona_emoji] _Reply with the *number* "
                        "of your chosen answer:_",
                        "",
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
                "next": "state_s1_3_sex_health_lit_right_to_sex",
            },
            "state_s1_3_sex_health_lit_right_to_sex": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Robert and Samantha have been dating for 5 years and love "
                        "each other very much.*",
                        "",
                        "Every year on Robert's birthday, "
                        "Samantha promises him sex for his birthday. This year, "
                        "Samantha tells Robert that she is too tired for sex.",
                        "",
                        "*_How much do you agree or disagree with this statement?_* 👇🏾",
                        "",
                        "Robert has the right to force Samantha to have sex.",
                        "",
                        "_*Tap the button* below and select the option "
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
                "next": "state_s1_4_sex_health_lit_insist_condoms",
            },
            "state_s1_4_sex_health_lit_insist_condoms": {
                "type": "list",
                "text": "\n".join(
                    [
                        "How much do you agree or disagree with "
                        "the following statement:",
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
                    ("not_active", "I am not sexually active"),
                ],
                "next": "state_s1_5_sex_health_lit_saying_no",
            },
            "state_s1_5_sex_health_lit_saying_no": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*If you are in a relationship, which statement describes you "
                        "best?*",
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
                "next": "state_s1_6_sex_health_lit_needs_important",
            },
            "state_s1_6_sex_health_lit_needs_important": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How true does this statement sound to you?*",
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
                "next": "state_s1_7_sex_health_lit_own_pleasure",
            },
            "state_s1_7_sex_health_lit_own_pleasure": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How true does this statement sound to you?*",
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
                "next": "state_s1_8_sex_health_lit_contraception_1",
            },
            "state_s1_8_sex_health_lit_contraception_1": {
                "text": "*During the last time you had sex, did you or your partner "
                "do something or use any method to avoid or delay getting pregnant?*",
                "type": "button",
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                ],
                "next": {
                    "yes": "state_s1_9_sex_health_lit_contraceptive_2",
                    "no": "state_s1_progress_complete",
                },
            },
            "state_s1_9_sex_health_lit_contraceptive_2": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*What has been the main method that you or your partner "
                        "have used to delay or avoid getting pregnant?*",
                        "",
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
                "next": "state_s1_progress_complete",
            },
            "state_s1_progress_complete": {
                "type": "info",
                "text": "\n".join(
                    [
                        "🏁 🎉",
                        "",
                        "Awesome. That's all the questions for now!",
                        "",
                        "🤦🏾‍♂️ Thanks for being so patient and honest 😌.",
                    ]
                ),
                "next": None,
            },
        },
    },
}
