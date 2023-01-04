Introduction
------------

For any contact fields that we need to store permanently, we store these in RapidPro. There is a `rapidpro.py` module which has helper methods for updating contact fields in RapidPro.

On every inbound message, we fetch these contact fields, and store them in `self.user.metadata`. So you should not use the `get_profile` method, rather used the fields cached in `self.user.metadata`. The `update_profile` method in `rapidpro.py` also updates the field in `self.user.metadata` to ensure that they stay in sync.

Fields
------

| Field name                                 | use                                                                                                     |
|--------------------------------------------|---------------------------------------------------------------------------------------------------------|
| assessment_reminder                        | Set a time to remind the user to take an assessment that they haven't started                           |
| assessment_reminder_name                   | Name of the assessment we need to remind the user to take                                               |
| sexual_health_lit_risk                     | save the risk status from sexual_health_lit assessment (high_risk or low_risk)                          |
| sexual_health_lit_score                    | save the score from sexual_health_lit assessment                                                        |
| depression_and_anxiety_risk                | save the risk status from depression and anxiety assessment (high_risk or low_risk)                     |
| depression_and_anxiety_score               | save the score from depression and anxiety assessment                                                   |
| connectedness_risk                         | save the risk status from connectedness assessment (high_risk or low_risk)                              |
| connectedness_score                        | save the score from connectedness assessment                                                            |
| gender_attitude_risk                       | save the risk status from gender attitude risk assessment (high_risk or low_risk)                       |
| gender_attitude_score                      | save the score from gender attitude risk assessment                                                     |
| body_image_risk                            | save the risk status from body image assessment (high_risk or low_risk)                                 |
| body_image_score                           | save the score from body image assessment                                                               |
| self_perceived_healthcare_risk             | save the risk status from self perceived healthcare assessment (high_risk or low_risk)                  |
| self_perceived_healthcare_score            | save the score from self perceived healthcare assessment                                                |
| feedback_timestamp                         | Save the timestamp at which the user should get a feedback quiz                                         |
| feedback_timestamp_2                       | Save the timestamp at which the user should get a feedback quiz used only for service finder feedback   |
| feedback_type                              | sets which feedback should be sent, options are `content`, `facebook_banner`, `service_finder`, `ask_a_question`, `ask_a_question_2` |
| feedback_type_2                            | sets which feedback should be sent, options are `servicefinder`, this is used to ask the user if they went to the facility they were looking for |
| feedback_survey_sent                       | Sets whether the feedback has been sent                                                                 |
| feedback_survey_sent_2                     | Sets whether the feedback has been sent                                                                 |
| age                                        | Age of the user                                                                                         |
| relationship_status                        | Relationship status of the user                                                                         |
| gender                                     | Gender of the user                                                                                      |
| location_description                       | Saves the `formatted_address` returned from the google location API                                     |
| latitude                                   | saves the users latitudinal position                                                                    |
| longitude                                  | saves the users longitudinal position                                                                   |
| persona_name                               | saves the users preferred bot persona name                                                              |
| persona_emoji                              | saves the users preferred bot persona emoji                                                             |
| last_mainmenu_time                         | saves the last time the user was on the mainmenu, set in mainmenu                                       |
| last_main_time                             | not being used - updated when `suggested_text` is updated, set in mainmenu                              |
| suggested_text                             | not being used - a list of content that the user might be interested in to encourage engagement         |
| privacy_reminder_sent                      | Set to True once the user has seen the main menu with a privacy message                                 |
| push_related_page_id                       | the Id of the push message's related page, the id of the page that will be sent when the user requests to read more |
| last_onboarding_time                       | saves the last time the user interacted with the onboarding flow                                        |
| onboarding_reminder_type                   | saves which onboarding reminder must be saved, 5min, 2h, 8h                                             |
| onboarding_reminder_sent                   | the onboarding reminder has been sent, resets when the user interacts with the onboarding reminder      |
| callback_check_time                        | saves the time the user should be sent the callback check in and find out if they were called           |
| callback_abandon_reason                    | saves the reason the user abandoned the call back in response to the callback check in                  |
| push_message_opt_in                        | saves whether the user would like daily messages, can be `True` or `False`                              |
| onboarding_completed                       | saves that the user has completed onboarding, can be `True` or blank                                    |
| opted_out                                  | saves that the user has opted out of the entire service                                                 |
| opted_out_timestamp                        | saves the datetime that the user opted out of the service                                               |
| terms_accepted                             | saves that the user has accepted the terms of service, , can be `True` or blank                         |
| engaged_on_facebook                        | saves that the user saw or did not see the recent facebook banner, can be `True` or `False`             |
| dob_month                                  | no longer collected                                                                                     |
| dob_day                                    | no longer collected                                                                                     |
| dob_year                                   | no longer collected                                                                                     |
| province                                   | no longer collected                                                                                     |
| suburb                                     | no longer collected                                                                                     |
| street_name                                | no longer collected                                                                                     |
| street_number                              | no longer collected                                                                                     |
| emergency_contact                          | save contact number on which the user can be called                                                     |
