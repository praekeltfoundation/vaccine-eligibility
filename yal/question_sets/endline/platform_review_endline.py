# Survey state naming convention
# [survey_name]_[subsection]_q[question]_topic
ASSESSMENT_QUESTIONS = {
    "1":
    # Platfrom Review
    {
        "start": "endline_12_q1_platform_review",
        "questions": {
            "endline_12_q1_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "You have received a lot of content from BWise.",
                        "",
                        "*Did BWise send you content that related to your "
                        "sexual needs?*",
                    ]
                ),
                "options": [
                    ("very_relatable", "Very relatable"),
                    ("relatable_well", "Related well"),
                    ("relatable_fine", "Related fine"),
                    ("relatable_little", "Related a little"),
                    ("dont_relate", "Didn't relate at all"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q2_platform_review",
            },
            "endline_12_q2_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*For the content that BWise sent you that related to"
                        " your needs, was the content that BWise sent you"
                        " interesting?*"
                    ]
                ),
                "options": [
                    ("very_interesting", "Very interesting"),
                    ("quite_interesting", "Quite interesting"),
                    ("kind_of", "Kind of interesting"),
                    ("hardly_really", "Hardly interesting"),
                    ("very_uninteresting", "Very uninteresting"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q3_platform_review",
            },
            "endline_12_q3_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How useful did you find the information the BWise"
                        " sent you for managing your sexual health and"
                        " relationship needs?*",
                    ]
                ),
                "options": [
                    ("extremely_useful", "Extremely useful"),
                    ("quite_useful", "Quite useful"),
                    ("kind_of_useful", "Kind of useful"),
                    ("not_really", "Not really useful"),
                    ("not at all", "Not at all useful"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q4_platform_review",
            },
            "endline_12_q4_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Did you know BWise is on Facebook and, if so, have you ever "
                        "visited their page?*",
                    ]
                ),
                "options": [
                    ("yes_weekly", "Yes, every week"),
                    ("yes_monthly", "Yes, every month"),
                    ("yes_no_much", "Yes, not that much"),
                    ("yes_never_user", "Yes, never used it"),
                    ("no", "No, didn't know that"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q5_platform_review",
            },
            "endline_12_q5_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Before joining B-Wise, how often did "
                        "you have discussions or interact with "
                        "content about sexual topics?*",
                    ]
                ),
                "options": [
                    ("a_lot", "A lot"),
                    ("somewhat", "Somewhat"),
                    ("not_much", "Not much"),
                    ("never", "Never"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q6_platform_review",
            },
            "endline_12_q6_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Since joining BWise, have you ever felt like you needed to "
                        "visit a health facility about your mental or sexual health?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": {
                    "yes": "endline_12_q6a_platform_review",
                    "no": "endline_12_q6e_platform_review",
                    "dont_understand": "endline_12_q6e_platform_review",
                    "skip_question": "endline_12_q6e_platform_review",
                },
            },
            "endline_12_q6a_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*How many times have you visited a clinic or other health "
                        "facility for your sexual health since joining BWise? (We "
                        "know it may be hard to remember, we`d appreciate your best "
                        "guess)*"
                    ]
                ),
                "options": [
                    ("none", "None"),
                    ("1", "1 time"),
                    ("2", "2 times"),
                    ("3", "3 times"),
                    ("4", "4 times"),
                    ("5", "5 times"),
                    ("6", "6 times"),
                    ("7", "7 times"),
                    ("8_or_more", "8 or more"),
                    ("skip_question", "Skip question"),
                ],
                "next": {
                    "none": "endline_12_q6c_platform_review",
                    "1": "endline_12_q6d_platform_review",
                    "2": "endline_12_q6d_platform_review",
                    "3": "endline_12_q6d_platform_review",
                    "4": "endline_12_q6d_platform_review",
                    "5": "endline_12_q6d_platform_review",
                    "6": "endline_12_q6d_platform_review",
                    "7": "endline_12_q6d_platform_review",
                    "8_or_more": "endline_12_q6d_platform_review",
                    "skip_question": "endline_12_q6e_platform_review",
                },
            },
            "endline_12_q6c_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Was there a reason you didn’t go to the clinic or other "
                        "health facility?*"
                    ]
                ),
                "options": [
                    ("where", "Didn`t know where"),
                    ("time", "Didn`t have time"),
                    ("money", "Didn`t have money "),
                    ("judgement", "Fear of judgement"),
                    ("bas_service", "Fear of bad service"),
                    ("elsewhere", "Got help elsewhere"),
                    ("no_need", "No longer needed"),
                    ("dont_understand", "I don`t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q6e_platform_review",
            },
            "endline_12_q6d_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*When you visited the clinic or other health facility, what "
                        "was the outcome? (If you had different experiences, please "
                        "pick the response that was true most of the time).*"
                    ]
                ),
                "options": [
                    ("got_help", "I got help"),
                    ("no_diagnosis", "Visited, no diagnosis"),
                    ("no_help", "Didn`t get help"),
                    ("dont_understand", "I don`t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q6e_platform_review",
            },
            "endline_12_q6e_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you think that your time on BWise has changed how likely "
                        "you are to visit a clinic or health facility for your sexual "
                        "and mental health?*"
                    ]
                ),
                "options": [
                    ("a_lot", "A lot more likely"),
                    ("little_more", "Little more likely"),
                    ("no_change", "No change"),
                    ("little_less", "Little less likely"),
                    ("lot_less", "A lot less likely"),
                    ("dont_understand", "I don`t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q7_platform_review",
            },
            "endline_12_q7_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Did you know you can use BWise WA to find a clinic "
                        "for you based on your needs?*",
                    ]
                ),
                "options": [
                    ("yes_used", "Yes, and I used it"),
                    ("yes_never_used", "Yes, never used it"),
                    ("no", "No, didn't know that"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q8_platform_review",
            },
            "endline_12_q8_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Did you ever go to one of the services that "
                        "BWise recommended?*",
                    ]
                ),
                "options": [
                    ("yes_got_help", "Yes, and got help"),
                    ("yes_got_no_help", "Yes, but wasn't helpful"),
                    ("no_too_far", "No, too far away"),
                    ("no_not_relevant", "No, not relevant"),
                    ("no_other_reason", "No, other reasons"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q9_platform_review",
            },
            "endline_12_q9_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Since joining BWise, have you ever felt like you "
                        "needed to speak to a counsellor about your mental "
                        "or sexual health?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q10_platform_review",
            },
            "endline_12_q10_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Did you know you can request a callback from a LoveLife "
                        "counsellor through the BWise WhatsApp chatbot?*"
                    ]
                ),
                "options": [
                    ("yes_got_help", "Yes, and I got help"),
                    ("yes_no_help", "Yes, didn't help"),
                    ("yes_never_used", "Yes, never used it"),
                    ("no", "No, didn't know that"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q10b_platform_review",
            },
            "endline_12_q10b_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Other than using LoveLife, have you visited another mental "
                        "or sexual health counselor (since joining BWise) and if so, "
                        "how many times? (We know it may be hard to remember, we`d "
                        "appreciate your best guess)*"
                    ]
                ),
                "options": [
                    ("none", "None"),
                    ("1", "1 time"),
                    ("2", "2 times"),
                    ("3", "3 times"),
                    ("4", "4 times"),
                    ("5", "5 times"),
                    ("6_or_more", "6 or more"),
                    ("none_but_needed", "None but needed to"),
                    ("dont_understand", "I don't understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": {
                    "none": "endline_12_q10c_platform_review",
                    "1": "endline_12_q10c_platform_review",
                    "2": "endline_12_q10c_platform_review",
                    "3": "endline_12_q10c_platform_review",
                    "4": "endline_12_q10c_platform_review",
                    "5": "endline_12_q10c_platform_review",
                    "6_or_more": "endline_12_q10c_platform_review",
                    "none_but_needed": "endline_12_q10d_platform_review",
                    "dont_understand": "endline_12_q10c_platform_review",
                    "skip_question": "endline_12_q10c_platform_review",
                },
            },
            "endline_12_q10c_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*Do you think that your time on BWise has changed how likely "
                        "you are to speak to a counsellor about your mental or sexual "
                        "health?*"
                    ]
                ),
                "options": [
                    ("a_lot", "A lot more likely"),
                    ("little_more", "Little more likely"),
                    ("no_change", "No change"),
                    ("little_less", "Little less likely"),
                    ("lot_less", "A lot less likely"),
                    ("dont_understand", "I don`t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": None,
            },
            "endline_12_q10d_platform_review": {
                "type": "list",
                "text": "\n".join(
                    [
                        "*What was the main reason you didn`t speak to a counsellor "
                        "about your mental or sexual health?*"
                    ]
                ),
                "options": [
                    ("where", "Didn`t know where"),
                    ("time", "Didn`t have time"),
                    ("money", "Didn`t have money "),
                    ("judgement", "Fear of judgement"),
                    ("bas_service", "Fear of bad service"),
                    ("elsewhere", "Got help elsewhere"),
                    ("no_need", "No longer needed"),
                    ("dont_understand", "I don`t understand"),
                    ("skip_question", "Skip question"),
                ],
                "next": "endline_12_q10c_platform_review",
            },
        },
    },
}
