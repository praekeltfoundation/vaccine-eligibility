# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Sexual consent
    {
        "start": "endline_10_q1_sexual_consent",
        "questions": {
            "endline_10_q1_sexual_consent": {
                "type": "list",
                "text": "\n".join(
                    [
                        "Robert and Samantha have been dating for 5 years and "
                        "love each other very much. 👩🏾‍❤️‍👨🏾",
                        "",
                        "Every year on Robert's birthday, Samantha promises "
                        "him sex for his birthday. This year, Samantha tells "
                        "Robert that she is too tired for sex. ",
                        "",
                        "*To what extent do you agree with this statement:*",
                        "",
                        "Robert has the right to force Samantha to have sex.",
                    ]
                ),
                "options": [
                    ("strongly_agree", "Strongly agree"),
                    ("agree", "Agree"),
                    ("not_sure", "Not Sure"),
                    ("disagree", "Disagree"),
                    ("strongly_disagree", "Strongly disagree"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "strongly_agree": 1,
                    "agree": 2,
                    "not_sure": 3,
                    "disagree": 4,
                    "strongly_disagree": 5,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_10_q2_sexual_consent",
            },
            "endline_10_q2_sexual_consent": {
                "type": "choice",
                "text": "\n".join(
                    [
                        "*If you're in a relationship, which of these statements "
                        "describes you best?*",
                        "",
                        "Please respond with the *number* of one of the options "
                        "below *e.g. 3* ",
                    ]
                ),
                "options": [
                    (
                        "comfortable_with_saying_no",
                        "I feel comfortable telling my partner no if they want "
                        "to have sex, but I do not want to",
                    ),
                    (
                        "hard_to_say_no",
                        "I find it difficult to tell my partner 'no' if they "
                        "want to have sex but I do not want to",
                    ),
                    ("not_sure_how_feel", "I’m not sure"),
                    ("not_in_relationship", "I’m not in a relationship"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "scoring": {
                    "comfortable_with_saying_no": 5,
                    "hard_to_say_no": 1,
                    "not_sure_how_feel": 2,
                    "not_in_relationship": 3,
                    "dont_understand": 1,
                    "skip_question": 1,
                },
                "next": "endline_10_q3_sexual_consent",
            },
            "endline_10_q3_sexual_consent": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Which of these has most influenced your attitudes about "
                        "sexual relationships and interactions?*",
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
                ],
                "next": {
                    "other": "endline_10_q3B_sexual_consent",
                    "social_media": None,
                    "bwise_whatsapp": None,
                    "bwise_facebook": None,
                    "friends_partner": None,
                    "school_university": None,
                    "health_facility": None,
                    "tv_radio": None,
                },
            },
            "endline_10_q3B_sexual_consent": {
                "type": "text",
                "text": "\n".join(
                    [
                        "*Do you mind telling us what has most"
                        " influenced your attitudes about sexual"
                        " relationships and interactions?*",
                    ]
                ),
                "next": None,
            },
        },
    },
}
