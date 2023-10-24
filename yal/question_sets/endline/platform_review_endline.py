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
                        "*Did you know BWise is on Facebook and, if so, "
                        "have you ever visited?*",
                    ]
                ),
                "options": [
                    ("yes_weekly", "Yes, every week"),
                    ("yes_monthly", "Yes, every month"),
                    ("yes_no_much", "Yes, not that much"),
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
                        "*Since joining BWise, have you ever felt like you needed "
                        "to see a medical service about your mental or sexual health?*",
                    ]
                ),
                "options": [
                    ("yes", "Yes"),
                    ("no", "No"),
                    ("dont_understand", "I don't understand"),
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
                        "*Did you know you can request a callback from a "
                        "LoveLife counsellor "
                        "through the B-Wise WhatsApp chatbot?*"
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
                "next": None,
            },
        },
    },
}
