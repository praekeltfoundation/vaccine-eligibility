
### Update profile flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                               |
|--------------------------------------------|--------------------|--------------|---------------------------|------------------------------------------------------------------------------------------|
| state_display_preferences                  |        TRUE        |     Text     |            TRUE           | Displays profile fields to user. User response is which field to update                                           |
| state_update_age                           |        TRUE        |     Int      |            TRUE           | Asks user to enter their age                                                                                       |
| state_update_age_confirm                   |        TRUE        |     Text     |            TRUE           | Asks user to confirm new age choice. User response is "yes" or "no"                                                |
| state_update_age_submit                    |        FALSE       |              |            FALSE          | Updates user profile with new age                                                                              |
| state_conclude_changes                     |        TRUE        |     Text     |            TRUE           | Offers user other features. User response is "menu" or "state_aaq_start"                                    |
| state_update_relationship_status           |        TRUE        |     Text     |            TRUE           | Asks user to enter their relationship status. User response is "yes", "complicated", "no" or "skip"                |
| state_update_relationship_status_confirm   |        TRUE        |     Text     |            TRUE           | Asks user to confirm new relationship status choice. User response is "yes" or "no"                                |
| state_update_relationship_status_submit    |        FALSE       |              |            TRUE           | Updates user profile with new relationship status                                                              |
| state_update_location                      |        TRUE        |     ????     |            TRUE           | Asks user to share a location pin                                                                              |
| state_get_updated_description_from_coords  |        FALSE       |              |            FALSE          | Queries Google Places API for name of location from lat and long of pin                                         |
| state_update_location_confirm              |        TRUE        |     Text     |            TRUE           | Asks user to confirm location description. User response is "yes" or "no"                                      |
| state_update_location_submit               |        FALSE       |              |            TRUE           | Updates user profile with new latitude, longitude and location description                                     |
| state_update_gender                        |        TRUE        |     Text     |            TRUE           | Asks user to enter their gender. User response is "female", "male", "non_binary", "other" or "rather_not_say"      |
| state_update_other_gender                  |        TRUE        |     Text     |            TRUE           | Asks user to enter their gender using free text                                                                    |
| state_update_gender_confirm                |        TRUE        |     Text     |            TRUE           | Asks user to confirm new gender choice. User response is "yes" or "no"                                             |
| state_update_gender_submit                 |        FALSE       |              |            TRUE           | Updates user profile with new gender choices                                                                   |
| state_update_bot_name                      |        TRUE        |     Text     |            TRUE           | Asks user to enter a custom name for the bot                                                                   |
| state_update_bot_name_submit               |        FALSE       |              |            FALSE          | Updates user profile with new bot name                                                                         |
| state_update_bot_emoji                     |        TRUE        |     Text     |            TRUE           | Asks user to enter an emoji to represent the bot                                                                |
| state_update_bot_emoji_submit              |        TRUE        |     Text     |            TRUE           | Updates user profile with new bot emoji and offers other features. User response is "menu" or "ask_a_question" |
| state_update_notifications_turn_off        |        TRUE        |     Text     |            TRUE           | Asks user if they would like to turn off daily messages |
| state_update_notifications_turn_off_submit |        FALSE       |              |            FALSE          | Updates user profile to turn off daily messages |
| state_update_notifications_turn_on         |        TRUE        |     Text     |            TRUE           | Asks user if they would like to turn on daily messages |
| state_update_notifications_turn_on_submit  |        FALSE       |              |            FALSE          | Updates user profile to turn on daily messages |
| state_update_notifications_final           |        TRUE        |     Text     |            TRUE           | After updating the profile, asks user what they would like to do next, go to main menu or AAQ |
| state_update_study_optout                  |        TRUE        |     Text     |            FALSE          | Update user profile to opt out of study
| study_optout_confirm                       |        TRUE        |     Text     |            FALSE          | Confirms user is no longer part of study Offers user other features. User response is "menu" or "state_aaq_start"
### AAQ flows
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                       |
|--------------------------------------------|--------------------|--------------|---------------------------|------------------------------------------------------------------------------|
| state_aaq_start                            |        TRUE        |     Text     |            TRUE           | Asks user to enter a question. Can be called with buttons defined                                  |
| state_coming_soon                          |        FALSE       |              |            FALSE          | End state. Informs user that aaq isn't available                                                      |
| state_set_aaq_timeout_1                    |        FALSE       |              |            TRUE           | Sets feedback timeout for AAQ list                                                                  |
| state_aaq_model_request                    |        FALSE       |              |            FALSE          | Sends user question to AAQ model                                                                     |
| state_no_answers                           |        FALSE       |              |            TRUE           | Takes user back to state_aaq_start                                                               |
| state_aaq_get_page                         |        FALSE       |              |            FALSE          | Retrieves the data for the aaq page chosen by the user                                               |
| state_display_results                      |        TRUE        |     Text     |            TRUE           | Shows user the choice of answers to their AAQ question. User response is title of answer to view       |
| state_set_aaq_timeout_2                    |        FALSE       |              |            TRUE           | Sets feedback timeout for AAQ answer page                                                           |
| state_display_content                      |        FALSE       |              |            TRUE           | Shows user chosen AAQ page. Takes user to state_get_content_feedback                                |
| state_get_content_feedback                 |        TRUE        |     Text     |            TRUE           | Asks user if AAQ page was useful. User response is "yes", "no" or "back to list"                    |
| state_is_question_answered                 |        FALSE       |              |            TRUE           | Sends AAQ page feedback to model. Routes user based on state_get_content_feedback response            |
| state_yes_question_answered                |        TRUE        |     Text     |            TRUE           | Asks user for any changes to AAQ page. User response is "yes" or "no"                           |
| state_yes_question_answered_no_changes     |        TRUE        |     Text     |            TRUE           | Offers user other features. User response is "aaq" or "counsellor"                              |
| state_yes_question_answered_changes        |        TRUE        |     Text     |            TRUE           | Asks user to detail changes to AAQ page                                                           |
| state_no_question_not_answered             |        TRUE        |     Text     |            TRUE           | Asks user to detail what they were looking for                                                         |
| state_no_question_not_answered_thank_you   |        TRUE        |     Text     |            TRUE           | Offers user other features. User response is "clinic" or "counsellor"                           |
| state_handle_list_timeout                  |        TRUE        |     Text     |            TRUE           | Timeout sent if user doesn't pick an AAQ page. Offers to ask again. User response is "yes" or "no" |
| state_handle_timeout_response              |        FALSE       |              |            TRUE           | Routes user based on what timeout they are responding to                                           |
| state_aaq_timeout_unrecognised_option      |        TRUE        |     Text     |            TRUE           | Offers user options when we didn't recognise feedback response. User response is "feedback", "mainmenu" or "aaq" |


### Content Feedback flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                             |
|--------------------------------------------|--------------------|--------------|---------------------------|----------------------------------------------------------------------------------------|
| state_content_feedback_survey_start        |        FALSE       |              |            TRUE           | Resets feedback timer fields on contact profile                                                               |
| state_content_feedback_unrecognised_option |        TRUE        |     Text     |            TRUE           | Offers user options when we didn't recognise feedback response. User response is "feedback", "mainmenu" or "aaq" |
| state_process_content_feedback_trigger     |        TRUE       |      Text     |            TRUE           | Timeout sent after user reads browsable content. Asks if the content was useful. User response is "yes" or "no" |
| state_positive_feedback                    |        TRUE       |      Text     |            TRUE           | Asks user for any changes to content. User response is "yes" or "no"                                      |
| state_no_feedback                          |        TRUE       |      Text     |            TRUE           | Offers user other features. User response is "counsellor", "question" or "update info"                    |
| state_get_feedback                         |        TRUE        |     Text     |            TRUE           | Asks user to detail changes to content                                                                      |
| state_confirm_feedback                     |        TRUE        |     Text     |            TRUE           | Offers user other features. User response is "counsellor", "question" or "update info"                    |
| state_negative_feedback                    |        TRUE        |     Text     |            TRUE           | Offers user Ask a Question feature. User response is "yes" or "no"                                        |
| state_no_negative_feedback                 |        TRUE        |     Text     |            TRUE           | Offers user other features. User response is "counsellor", "question" or "update info"                    |


### Main states
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                             |
|--------------------------------------------|--------------------|--------------|---------------------------|----------------------------------------------------------------------------------------|
| state_qa_reset_feedback_timestamp_keywords |        FALSE       |              |            FALSE          | State intended for QA purposes. Resets feedback timestamps. Triggered by an obscure keyword                   |
| state_start                                |        FALSE       |              |            TRUE           | Session entry state. Routes user based on the message they sent in                                           |
| state_catch_all                            |        FALSE       |              |            TRUE           | Sends user a generic welcome message if we received input we don't recognise                                 |
| state_error                                |        FALSE       |              |            TRUE           | Closes user session                                 |
| state_sexual_health_literacy_assessment    |        FALSE       |              |            FALSE          |  Starts the sexual health literacy assessment |
| state_locus_of_control_assessment | FALSE | |  FALSE |  Starts the locus of control assessment |
| state_depression_and_anxiety_assessment | FALSE | |  FALSE |  Starts the depression and anxiety assessment |
| state_connectedness_assessment | FALSE | |  FALSE |  Starts the connectedness assessment |
| state_gender_attitude_assessment | FALSE | |  FALSE |  Starts the gender attitude assessment |
| state_body_image_assessment | FALSE | |  FALSE |  Starts the body image assessment |
| state_self_perceived_healthcare_assessment | FALSE | |  FALSE |  Starts the self perceived healthcare assessment |
| state_self_esteem_assessment | FALSE | |  FALSE |  Starts the self esteem assessment |
| state_gender_attitude_assessment_risk_message | FALSE | |  FALSE |  End message for gender attitude assessments |
| state_self_perceived_healthcare_assessment_risk_message | FALSE | |  FALSE |  End message for self perceived healthcare assessments |
| state_connectedness_assessment_end | FALSE | |  FALSE |  Update connectedness_risk and connectedness_score on contact field |
| state_sexual_health_literacy_assessment_end | FALSE | |  FALSE |  Update sexual_health_literacy_risk and sexual_health_literacy_score on contact field |
| state_depression_and_anxiety_assessment_risk_message | FALSE | |  FALSE |  End message for depression and anxiety assessments |
| state_body_image_assessment_end | FALSE | |  FALSE |  Update body_image_risk and body_image_score on contact field |
| state_depression_and_anxiety_assessment_end | FALSE | |  FALSE |  Update depression_and_anxiety_risk and depression_and_anxiety_score on contact field |
| state_connectedness_assessment_risk_message | FALSE | |  FALSE |  End message for connectedness assessments |
| state_body_image_assessment_risk_message | FALSE | |  FALSE |  End message for body image assessments |
| state_self_perceived_healthcare_assessment_end | FALSE | |  FALSE |  Update self_perceived_healthcare_risk and self_perceived_healthcare_score on contact field |
| state_gender_attitude_assessment_end | FALSE | |  FALSE |  Update gender_attitude_risk and gender_attitude_score on contact field |
| state_depression_and_anxiety_risk | FALSE | Text |  TRUE  |  Save depression and anxiety risk to flow results |
| state_depression_and_anxiety_score | FALSE | Text |  TRUE  |  Save depression and anxiety score to flow results |
| state_connectedness_risk | FALSE | Text |  TRUE  |  Save connectedness risk to flow results |
| state_connectedness_score | FALSE | Text |  TRUE  |  Save connectedness score to flow results |
| state_gender_attitude_risk | FALSE | Text |  TRUE  |  Save gender attitude risk to flow results |
| state_gender_attitude_score | FALSE | Text |  TRUE  |  Save gender attitude score to flow results |
| state_body_image_risk | FALSE | Text |  TRUE  |  Save body image risk to flow results |
| state_body_image_score | FALSE | Text |  TRUE  |  Save body image score to flow results |
| state_self_perceived_healthcare_risk | FALSE | Text |  TRUE  |  Save self perceived healthcare risk to flow results |
| state_self_perceived_healthcare_score | FALSE | Text |  TRUE  |  Save self perceived healthcare score to flow results |
| state_sexual_health_lit_risk | TRUE | Text | TRUE | Sexual health literacy risk |
| state_sexual_health_lit_score | TRUE | Number | TRUE | Score from sexual health literacy assessment |
| state_locus_of_control_assessment_later |  |  |  | Update name of the locus_of_control assessment to the metadata |
| state_sexual_health_literacy_assessment_later |  |  |  | Update name of the sexual_health_literacy assessment to the metadata |
| state_depression_and_anxiety_assessment_later |  |  |  | Update name of the depression_and_anxiety assessment to the metadata |
| state_connectedness_assessment_later |  |  |  | Update name of the connectedness assessment to the metadata |
| state_gender_attitude_assessment_later |  |  |  | Update name of the gender_attitude assessment to the metadata |
| state_body_image_assessment_later |  |  |  | Update name of the body_image assessment to the metadata |
| state_self_perceived_healthcare_assessment_later |  |  |  | Update name of the self_perceived_healthcare assessment to the metadata |
| state_source_tracking | TRUE | Text | TRUE | The trigger keyword that was used |
| state_generic_what_would_you_like_to_do | TRUE | Text | TRUE | state that asks the user what they would like to do, go to main menu, aaq or update settings |

### Main Menu flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_pre_mainmenu                         |        FALSE       |              |            TRUE          | Resets suggested content value for user's session                                                         |
| state_mainmenu                             |        TRUE        |     Text     |            TRUE          | Offers the main menu to the user. User response is the feature they want to view                         |
| state_check_relationship_status_set        |        FALSE       |              |            FALSE         | Checks if the user has shared their relationship status with us                                         |
| state_relationship_status                  |        TRUE        |     Text     |            TRUE          | Asks the user to enter their relationship status. User response is "yes", "no", "complicated" or "skip" |
| state_relationship_status_submit           |        FALSE       |              |            FALSE         | Updates user profile with relationship status chosen                                                       |
| state_contentrepo_page                     |        FALSE       |              |            TRUE          | Retrieves the details for the page chosen by the user                                                      |
| state_display_page                         |        TRUE        |              |            TRUE          | Sends user the page they chose. User response is based on content from content repo                       |
| state_get_suggestions                      |        FALSE       |              |            TRUE          | Updates the suggested content in the cache                                                             |
| state_display_suggestions                  |        TRUE        |     Text     |            TRUE          | Offers user the suggested content stored. User response is based on the content                            |
| state_back                                 |        FALSE       |              |            TRUE          | Sends the user back to the previous page                                                                |
| state_prep_push_msg_related_page           |        FALSE       |              |            FALSE         | Gets the id of the page the user's push message directed them to and sends them to state_display_page to view it |


### Onboarding flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_persona_name                         |        TRUE        |     Text     |            TRUE          | Asks user to enter a custom name for the bot                                                              |
| state_save_persona_name                    |        FALSE       |              |            TRUE          | Updates user profile with the new name                                                                         |
| state_persona_emoji                        |        TRUE        |     Text     |            TRUE          | Asks user to enter an emoji to represent the bot                                                           |
| state_save_persona_emoji                   |        FALSE       |              |            FALSE         | Updates user profile with the new emoji                                                                        |
| state_profile_intro                        |        FALSE       |              |            FALSE         | Sends a message to thank and set expectations                                                                 |
| state_age                                  |        TRUE        |     Int      |            TRUE          | Asks user to enter their age                                                                                  |
| state_gender                               |        TRUE        |     Text     |            TRUE          | Asks user to enter their gender. User response is "female", "male", "non_binary", "none of these" or "rather_not_say" |
| state_submit_onboarding                    |        FALSE       |     Text     |            TRUE          | Adds onboarding choices to user profile                                                                      |
| state_onboarding_complete                  |        FALSE       |              |            TRUE          | Redirects user to AAQ start state in case they want to ask a question                                      |
| state_stop_onboarding_reminders            |        TRUE        |     Text     |            TRUE          | Resets fields used for onboarding reminders                                                                 |
| state_reschedule_onboarding_reminders      |        TRUE        |     Text     |            TRUE          | Sets onboarding reminder fields so that reminder is resent later                                              |
| state_handle_onboarding_reminder_response  |        TRUE        |     Text     |            TRUE          | Routes user to other state based on their response to the onboarding reminder                              |
| state_rel_status                           |        TRUE        |     Text     |            TRUE          | Asks the user for their current relationship states, user response is "relationship", "single", "complicated"
| state_locus_of_control_assessment_start     |        FALSE       |              |            FALSE         | Explains to the user what is going to happen next                                                                   |
| state_locus_of_control_assessment_few_qs    |        TRUE        |     Text     |            TRUE          | User responds "ok" when they start the assessment  |
| state_locus_of_control_assessment_end |        FALSE       |              |            FALSE         | User has completed the assessment and receives the end message |
| state_phase2_update_exising_user_profile |        FALSE       |              |            FALSE         | For phase 2 we need to send existing users back to onboarding so that they can take the assessments. This state handles the push message response and inserts them based on their profile (if their gender isn't set they go to state_gender, if it is set they go to state_rel_status) |
| state_country                              |        TRUE       |      Text        |            TRUE         | Asks the user if they are in South Africa. User response is "yes", "no" or "skip" |
| state_seen_before                          |        TRUE       |      Text        |            TRUE         | Asks the user if they have used the Bwise bot before. User response is "yes", "no" or "skip" |
| state_monthly_household_income               |        TRUE       |      Text        |            TRUE         | Asks the user what their total monthly household income is. Response is a numbered list  |


### OptOut flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_optout                               |        TRUE        |     Text     |            TRUE          | Asks the user what they would to do. User response is "stop notifications", "delete saved" or "skip"     |
| state_submit_optout                        |        FALSE       |              |            FALSE         | Resets fields used for reminders so any pending reminders are cancelled                                 |
| state_stop_notifications                   |        FALSE       |              |            TRUE          | Sends user a message and then routes them to state_optout_survey                                          |
| state_optout_survey                        |        TRUE        |     Text     |            TRUE          | Asks user why they opted out. User response is chosen from a list                                         |
| state_delete_saved                         |        TRUE        |     Text     |            TRUE          | Deletes profile data. User response is "see" to see the cleaned profile                                |
| state_tell_us_more                         |        TRUE        |     Text     |            TRUE          | Asks user why they opted out. User response is freeText                                                   |
| state_opt_out_no_changes                   |        TRUE        |     Text     |            TRUE          | Bids the user farewell and asks if the user would like to go to aaq or main menu                                                           |
| state_farewell_optout                      |        TRUE        |     Text     |            TRUE          | Bids the user farewell and asks if the user would like to go to aaq or main |


### Quiz flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_quiz_start                           |        FALSE       |              |            TRUE          | Resets session info about user's progress through quiz                                                     |
| state_quiz_question                        |        TRUE        |     Text     |            TRUE          | Sends the requested quiz question to the user. User response can be "callme", "menu", "redo" or others    |
| state_quiz_process_answer                  |        TRUE        |     Text     |            TRUE          | Processes the user's response to the quiz question and updates their score                            |
| state_quiz_answer_feedback                 |        TRUE        |     Text     |            TRUE          | Sends user feedback about their answer and a button to proceed to the next question                        |


### Terms and Conditions flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_welcome                              |        TRUE        |     Text     |            TRUE          | Welcomes the user and invites to create a profile. User response is "create"                           |
| state_terms                                |        TRUE        |     Text     |            TRUE          | Asks user to accept privacy policy. User response is "accept", "decline" or "read"                   |
| state_terms_pdf                            |        FALSE       |              |            TRUE          | Sends user terms and conditions as pdf and then routes back to state_terms                            |
| state_decline_confirm                      |        TRUE        |     Text     |            TRUE          | Asks user to confirm their decline of the T&Cs. User response is "accept" or "end"                    |
| state_decline_1                            |        FALSE       |              |            TRUE          | Informs user that their online safety is important. Routes to state_decline_2                            |
| state_decline_2                            |        TRUE        |     Text     |            TRUE          | Informs user of how to rejoin. User response is "hi"                                                    |
| state_submit_terms_and_conditions          |        FALSE       |              |            TRUE          | Update the user's profile and direct user to onboarding flows                                              |


### Please call me / Talk to a counsellor flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_please_call_start                    |        FALSE       |              |            TRUE          | Routes the user based on the current time                           |
| state_out_of_hours                         |        TRUE        |     Text     |            TRUE          | Informs user that is it after hours. User response is "help now" or "opening hours"                           |
| state_emergency                            |        TRUE        |     Text     |            TRUE          | Provides the user with an emergency number to call. User response is "see"                           |
| state_open_hours                           |        TRUE        |     Text     |            TRUE          | Shows user opening hours. User response is "ok" or "callback in hours"                           |
| state_in_hours_greeting                    |        FALSE       |              |            TRUE          | Explains what the callback feature is                           |
| state_in_hours                             |        TRUE        |     Text     |            TRUE          | Asks user if current number should be used for call. User response is "yes" or "specify"        |
| state_submit_callback                      |        FALSE       |              |            TRUE          | Calls the LoveLife API to request the callback        |
| state_save_time_for_callback_check         |        FALSE       |              |            TRUE          | Schedules a feedback message to be sent 2hrs later        |
| state_callback_confirmation                |        TRUE        |     Text     |            TRUE          | Informs user that call was requested. User response is "ok", "help" or "hours"        |
| state_callme_done                          |        FALSE       |              |            TRUE          | Closes the session        |
| state_specify_msisdn                       |        TRUE        |     Text     |            TRUE          | Asks user to enter the alternate number to use. User response is valid phone number       |
| state_confirm_specified_msisdn             |        TRUE        |     Text     |            TRUE          | Asks user to confirm that they want to use the given msisdn. User response is "yes" or "no"      |
| state_ask_to_save_emergency_number         |        TRUE        |     Text     |            TRUE          | Asks user if we can safe the alternate number. User response is "yes" or "no"      |
| state_save_emergency_contact               |        FALSE       |              |            TRUE          | Saves alternate number on user profile      |
| state_handle_callback_check_response       |        TRUE        |     Text     |            TRUE          | Feedback message asking if the call was received. User response is "yes", "missed" or "no"      |
| state_collect_call_feedback                |        TRUE        |     Text     |            TRUE          | Asks user if the call was useful. User response is "yes" or "no"      |
| state_call_helpful                         |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "question", "update" or "counsellor"      |
| state_call_not_helpful_feedback            |        TRUE        |     Text     |            TRUE          | Asks user what was wrong with the call. User response is free text      |
| state_call_not_helpful_try_again           |        TRUE        |     Text     |            TRUE          | Asks user if they would like to try another call. User response is "yes" or "no"      |
| state_call_not_helpful_try_again_declined  |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "question" or "update"      |
| state_no_callback_received                 |        FALSE       |              |            TRUE          | Sends user our appologies      |
| state_ask_to_call_again                    |        TRUE        |     Text     |            TRUE          | Asks user if they would like to try another call. User response is "yes", "another way" or "no"      |
| state_retry_callback_choose_number         |        TRUE        |     Text     |            TRUE          | Asks user what number we should use for the retry. User response is "whatsapp", "previously saved" or "another" |
| state_offer_saved_emergency_contact        |        TRUE        |     Text     |            TRUE          | Shows the user the saved number to get confirmation. User response is "yes" or "no" |
| state_help_no_longer_needed                |        TRUE        |     Text     |            TRUE          | Asks the user to confirm they no longer need help. User response is "yes", "long" or "changed mind" |
| state_got_help                             |        TRUE        |     Text     |            TRUE          | Directs user to the main menu. User response is "menu" |
| state_too_long                             |        TRUE        |     Text     |            TRUE          | Offers user other contact options. User response is "another way" or "menu" |
| state_changed_mind                         |        TRUE        |     Text     |            TRUE          | Offers user other contact options. User response is "another way" or "menu" |
| state_contact_bwise                        |        TRUE        |     Text     |            TRUE          | Offers user other contact details. User response is "facebook", "twitter" or "website" |
| state_facebook_page                        |        TRUE        |     Text     |            TRUE          | Sends user link to Facebook. User response is "menu" |
| state_twitter_page                         |        TRUE        |     Text     |            TRUE          | Sends user link to Twitter. User response is "menu" |
| state_website                              |        TRUE        |     Text     |            TRUE          | Sends user link to website. User response is "menu" |
| state_confirm_redirect_please_call_me      |        TRUE        |     Text     |            TRUE          | Confirms with a user whether they'd like to speak to a human if their response fuzzy matches an emergency keyword |


### Segmentation survey flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_survey_already_completed             |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "state_aaq_state" or "state_pre_mainmenu"             |
| state_survey_decline                       |        TRUE        |     Text     |            TRUE          | User declined survey. Offers user other features. User response is "state_aaq_state" or "state_pre_mainmenu" |
| state_start_survey                         |        FALSE       |              |            TRUE          | Sets user expectations |
| state_survey_start                      |        FALSE        |     |            | |
| state_survey_question                      |        TRUE        |     Text     |            TRUE          | Sends the user a survey question. User response is based on content |
| state_survey_process_answer                |        FALSE       |              |            TRUE          | Caches user answer and progresses the survey |
| state_survey_done                          |        TRUE        |     Text     |            TRUE          | Thanks user and directs them to claim their airtime. User response is "get_airtime" |
| state_trigger_airtime_flow                 |        FALSE       |              |            TRUE          | Starts the user on the airtime flow in RapidPro |
| state_prompt_next_action                   |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "state_aaq_start", "state_pre_mainmenu" or "state_no_airtime" |
| state_no_airtime                           |        FALSE       |              |            TRUE          | Thanks user and closes session |
| state_assessment_later_submit              |        FALSE       |              |            TRUE          | Submits assessment_reminder and assessment_name as contact fields for a later reminder to complete assessment |
| state_assessment_later                     |        TRUE        |     Text     |            TRUE          | Thanks user and asks the user if they'd like to go to the main menu |
| state_sexual_health_literacy_send_risk_message |    TRUE        |     Text     |            TRUE          | Sends the user a message based on their risk score, takes in "yes" and "no" |
| state_handle_assessment_reminder_response |    FALSE        |          |                      | Handles the response to the assessment reminders |
| state_stop_assessment_reminders_confirm |    TRUE        |     Text     |   TRUE    | Confirms that the user no longer wants assessment reminders |
| state_stop_assessment_reminders_clear_fields |    FALSE        |     Text     |   FALSE    |  Clears the users  assessment reminders, then send user on to next state to determine where they want to go
| state_stop_assessment_reminders |    TRUE        |     Text     |   TRUE    |  Sets the user to no longer get assessment reminders, asks user if they would like to go to menu or aaq |
| state_reschedule_assessment_reminder |    |    |    | Schedules the assessment reminders |
| state_remind_tomorrow |    TRUE        |     Text     |   TRUE    | Lets the user know we will remind them tomorrow, asks the user if they would like to go to the mainmenu |
| state_reminder_not_interested | True | Text | TRUE | Lets the user know that they will no longer be prt of the study |
| state_survey_validation | True | Text | TRUE | endline survey catch all validation |
 state_household_number_of_people | False | Text | Endline number of peopleing living in househould |
| state_household_number_of_people_eight_or_more | False | Text | Endline number of peopleing living in househould if more than 8 people |


### Service finder flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_servicefinder_start                  |        TRUE        |     Text     |            TRUE          | Asks if user wants to find services. User response is "yes"             |
| state_check_address                        |        FALSE       |              |            TRUE          | Routes user based on presence of existing address             |
| state_pre_confirm_existing_address         |        FALSE       |              |            TRUE          | Sends conversational message             |
| state_confirm_existing_address             |        TRUE        |     Text     |            TRUE          | Asks user to confirm if existing address is correct             |
| state_confirm_existing_address             |        TRUE        |     Text     |            TRUE          | Asks user to confirm if existing address is correct. User response is "yes" or "new"       |
| state_category_lookup                      |        FALSE       |              |            TRUE          | Calls service finder api to load categories       |
| state_pre_category_msg                     |        FALSE       |              |            TRUE          | Sends conversational message       |
| state_save_parent_category                 |        FALSE       |              |            TRUE          | Moves user down the category tree       |
| state_category                             |        TRUE        |     Text     |            TRUE          | Shows user the loaded categories to choose from. User response is based on categories      |
| state_service_lookup                       |        FALSE       |              |            TRUE          | Calls service finder api to find nearby services      |
| state_no_facilities_found                  |        TRUE        |     Text     |            TRUE          | Asks user to try again. User response is "state_location" or "state_category"      |
| state_display_facilities                   |        FALSE       |              |            TRUE          | Shows user the list of facilities and then closes the session      |
| state_pre_different_location               |        FALSE       |              |            TRUE          | Routes user to state_location with a different message     |
| state_location                             |        TRUE        |     ????     |            TRUE          | Asks user to share a location pin. User can also respond with "type address" instead           |
| state_get_description_from_coords          |        FALSE       |              |            TRUE          | Calls Google Places API to get description for the location           |
| state_save_location                        |        FALSE       |              |            TRUE          | Stores location details on user profile           |
| state_province                             |        TRUE        |     Text     |            TRUE          | Asks user to choose a province           |
| state_full_address                         |        TRUE        |     Text     |            TRUE          | Asks user to enter their neighbourhood and street name           |
| state_full_address                         |        TRUE        |     Text     |            TRUE          | Asks user to enter their neighbourhood and street name           |
| state_validate_full_address                |        TRUE        |     Text     |            TRUE          | Tries to process full address and saves answers state_suburb and state_street_name if successful |
| state_validate_full_address_error          |        TRUE        |     Text     |            TRUE          | Explains to user that we will collect each field separately. User response is "yes" or "no" |
| state_suburb                               |        TRUE        |     Text     |            TRUE          | Asks user to enter their suburb |
| state_street_name                          |        TRUE        |     Text     |            TRUE          | Asks user to enter their street name |
| state_cannot_skip                          |        TRUE        |     Text     |            TRUE          | Informs the user that the previous state is required for the feature. User response is "share" or "menu" |
| state_check_new_address                    |        FALSE       |              |            TRUE          | Calls Google Places API to place_id for entered address |
| state_address_coords_lookup                |        FALSE       |              |            TRUE          | Calls Google Places API to get coordinates for entered address |


### Service finder feedback survey flow
| state_name                                   | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|----------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_servicefinder_feedback_survey_start        |        FALSE       |              |            TRUE          | Resets scheduled message fields so it is only sent once            |
| state_process_servicefinder_feedback_trigger     |        TRUE        |     Text     |            TRUE          | Asks the user if the feature was useful. User response is "yes", "no" or "already_know"             |
| state_servicefinder_feedback_unrecognised_option |        TRUE        |     Text     |            TRUE          | Handles feedback timeout. Asks the user what to do. User response is "feedback", "mainmenu" or "aaq" |
| state_servicefinder_positive_feedback            |        TRUE        |     Text     |            TRUE          | Asks user for  suggestions. User response is free text             |
| state_servicefinder_negative_feedback            |        TRUE        |     Text     |            TRUE          | Asks user for suggestions. User response is free text             |
| state_servicefinder_already_know_feedback        |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq" or "pleasecallme"             |
| state_save_servicefinder_callback_2              |        FALSE       |              |            TRUE          | Schedules the second feedback message             |
| state_servicefinder_feedback_confirmation        |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq" or "pleasecallme"           |
| state_servicefinder_feedback_survey_2_start      |        TRUE        |     Text     |            TRUE          | Asks if user went to the clinic. User response is "yes" or "no"             |
| state_went_to_service                            |        TRUE        |     Text     |            TRUE          | Asks if user's visit to clinic was helpful. User response is "helped", "no_help_needed" or "no_help" |
| state_did_not_go_to_service                      |        TRUE        |     Text     |            TRUE          | Asks why the user didn't go. User response is "changed_mind", "will_go", "elsewhere" or "other" |
| state_service_helped                             |        TRUE        |     Text     |            TRUE          | Asks if user has enough info. User response is "yes", "no" or "not_sure"             |
| state_service_no_help_needed                     |        TRUE        |     Text     |            TRUE          | Asks user to rate the clinic service. User response is "good", "ok" or "bad"             |
| state_service_no_help                            |        TRUE        |     Text     |            TRUE          | Asks user why they didn't get helped. User response is "queue", "other_help" or "other"             |
| state_have_information_needed                    |        TRUE        |     Text     |            TRUE          | Asks if user has enough info. User response is "yes", "no" or "not_sure"             |
| state_service_finder_survey_complete             |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq" or "pleasecallme"             |
| state_service_finder_offer_aaq                   |        TRUE        |     Text     |            TRUE          | Asks if user wants to use AAQ feature. User response is "yes" or "no"             |
| state_get_appointment_tips                       |        FALSE       |              |            TRUE          | Routes user to the content page for appointment tips             |
| state_offer_appointment_tips                     |        TRUE        |     Text     |            TRUE          | Asks if user wants tips for their next appointment. User response is "yes" or "no"             |
| state_offer_appointment_tips_bad_experience      |        TRUE        |     Text     |            TRUE          | Asks if user wants tips for their next appointment. User response is "yes" or "no"             |
| state_offer_clinic_finder                        |        TRUE        |     Text     |            TRUE          | Asks if user wants to find another clinic. User response is "yes" or "no"             |
| state_got_other_help                             |        TRUE        |     Text     |            TRUE          | Asks if user has enough info. User response is "yes", "no" or "not_sure"             |
| state_other_reason_for_no_service                |        TRUE        |     Text     |            TRUE          | Asks for 'other' reason the user didn't go. User response is free text             |
| state_service_finder_survey_complete_2           |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq" or "pleasecallme"             |
| state_offer_aaq                                  |        TRUE        |     Text     |            TRUE          | Asks if user wants to use AAQ feature. User response is "yes" or "no"             |
| state_service_finder_survey_complete_3           |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq",  "pleasecallme" or "servicefinder"             |
| state_service_finder_survey_complete_4           |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "aaq" or  "pleasecallme"             |
| state_service_finder_survey_complete_5           |        TRUE        |     Text     |            TRUE          | Asks if user wants to use AAQ feature. User response is "yes" or "no"             |


### Facebook crossover feedback flow
| state_name                                   | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|----------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_crossover_feedback_survey_start              |        FALSE       |              |            TRUE          | Resets scheduled message fields so it is only sent once            |
| state_wa_fb_crossover_feedback                     |        TRUE        |     Text     |            TRUE          | Asks user if they have engaged on facebook. User response is "yes" or "no"            |
| state_wa_fb_crossover_feedback_unrecognised_option |        TRUE        |     Text     |            TRUE          | Handles feedback timeout. Asks the user what to do. User response is "feedback", "mainmenu" or "aaq" |
| state_saw_recent_facebook                          |        TRUE        |     Text     |            TRUE          | Asks use if the content on facebook was helpful. User response is "helpful", "learnt new", "enjoyed comments" or "other" |
| state_not_saw_recent_facebook                      |        FALSE       |              |            TRUE          | Links user to facebook and closes session |
| state_fb_hot_topic_helpful                         |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "counsellor" or  "question"            |
| state_fb_hot_topic_enjoyed_comments                |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "counsellor" or  "question"            |
| state_fb_hot_topic_other                           |        TRUE        |     Text     |            TRUE          | Asks the user for the thoughts on the topic. User response is free text            |
| state_fb_hot_topic_thanks_for_feedback             |        TRUE        |     Text     |            TRUE          | Offers user other features. User response is "counsellor" or  "question"            |


### User testing feedback flow
| state_name                                   | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|----------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_check_feedback                 |        FALSE       |              |            TRUE          | Checks if we are still awaiting feedback from this user            |
| state_already_completed              |        FALSE       |              |            TRUE          | Closes the user session            |
| state_feedback_pleasecallme          |        TRUE        |     Text     |            TRUE          | Asks user to rate the please call me feature            |
| state_feedback_servicefinder         |        TRUE        |     Text     |            TRUE          | Asks user to rate the service finder feature            |
| state_feedback_changepreferences     |        TRUE        |     Text     |            TRUE          | Asks user to rate the change preferences feature            |
| state_feedback_quickreply            |        TRUE        |     Text     |            TRUE          | Asks user to rate their experience responding with quick replies            |
| state_feedback_numberskeywords       |        TRUE        |     Text     |            TRUE          | Asks user to rate their experience responding with numbers            |
| state_feedback_usefulinformation     |        TRUE        |     Text     |            TRUE          | Asks user to rate how useful the information was            |
| state_feedback_lookforinformation    |        TRUE        |     Text     |            TRUE          | Asks user to rate likelihood of using the chatbot for info in future            |
| state_feedback_willreturn            |        TRUE        |     Text     |            TRUE          | Asks user to rate likelihood of using YAL/Bwise in future            |
| state_submit_completed_feedback      |        FALSE       |              |            TRUE          | Starts a flow in rapidpro to save the user's feedback            |
| state_completed_feedback             |        TRUE        |     Text     |            TRUE          | Closes the user session            |

### PushMessages and Study OptIn flow
| state_name                                   | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|----------------------------------------------|--------------------|--------------|---------------------------|----------------------------------------------------------------------------------|
| state_start_pushmessage_optin                |        TRUE        |     Text     |            TRUE          | Asks user if they would like to receive push messages, answers include yes and no |
| state_pushmessage_optin_yes_submit           |        FALSE       |              |            TRUE          | Updates opted_in with True if user responds yes                                   |
| state_pushmessage_optin_yes                  |        TRUE        |     Text     |            TRUE          | Sends the user confirmation that they will receive push messages |
| state_pushmessage_optin_no_submit            |        FALSE       |              |            TRUE          | Updates opted_in with False if user responds no                                   |
| state_pushmessage_optin_no                   |        TRUE        |     Text     |            TRUE          | Sends the user confirmation that they will not receive push messages |
| state_pushmessage_optin_final                |        TRUE        |     Text     |            TRUE          | asks if user would like to go to main menu or aaq |
| state_is_eligible_for_study                  |        FALSE        |     Text     |            TRUE          | This is not a real state but where we save the outcome of the validation check to determine if the user is eligible for the study. Either "true" or "false" |
| state_study_invitation                        |        TRUE        |     Text     |            TRUE          | asks if user would like to be part of the EJAF study. Options are "yes" or "no" |
| state_study_consent                          |        TRUE        |     Text     |            TRUE          | asks the user to accept the T&Cs for the EJAF study. Options are "yes" or "no" |
| state_study_consent_yes_submit               |        FALSE        |     Text     |            FALSE          | Updates ejaf_study_optin with True if user responded yes to state_study_consent |
| state_study_consent_pdf                        |        FALSE        |     Text     |            FALSE          | Sends user terms and conditions as pdf and then routes them to the baseline survey |

### A1 Sexual health literacy assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a1_q1_sexual_health_lit | TRUE | Text | People can reduce the risk of getting STIs by |
| state_a1_q2_sexual_health_lit | TRUE | Text | If Teddy goes out to a restaurant and starts chatting with someone he is sexually attracted to, what is most appropriate way Teddy can tell that person wants to have sex with him? |
| state_a1_q3_sexual_health_lit | TRUE | Text | Robert has the right to force Samantha to have sex. |
| state_a1_q4_sexual_health_lit | TRUE | Text | If sexually active, I _am_ able to insist on condoms when I have sex. |
| state_a1_q5_sexual_health_lit | TRUE | Text | If you are in a relationship, which statement describes you best? |
| state_a1_q6_sexual_health_lit | TRUE | Text | My sexual needs or desires are important. |
| state_a1_q7_sexual_health_lit | TRUE | Text | I think it would be important to focus on my own pleasure as well as my partner's during sexual experiences. |
| state_a1_q8_sexual_health_lit | TRUE | Text | I expect to enjoy sex. |
| state_a1_q9A_sexual_health_lit | TRUE | Text | During the last time you had sex, did you or your partner do something or use any method to avoid or delay getting pregnant? |
| state_a1_q9B_sexual_health_lit | TRUE | Text | What's been the MAIN way you or your partner have tried to delay or avoid getting pregnant? |
|

### A2 Locus of control
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a2_1_q1_loc_of_ctrl | TRUE | Text | I'm my own boss. |
| state_a2_1_q2_loc_of_ctrl | TRUE | Text | If I work hard, I will be successful. |
| state_a2_1_q3_loc_of_ctrl | TRUE | Text | I CAN get relevant health advice if and when I want it. |
| state_a2_1_q4_loc_of_ctrl | TRUE | Text | What I do mainly depends on other people. |
| state_a2_1_q5_loc_of_ctrl | TRUE | Text | Fate often gets in the way of my plans. |

### A3 Depression and anxiety
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a3_q1_depression | TRUE | Text | Feeling nervous, anxious or on edge. |
| state_a3_q2_depression | TRUE | Text | Not being able to stop or control worrying. |
| state_a3_q3_depression | TRUE | Text | Feeling down, depressed or hopeless |
| state_a3_q4_depression | TRUE | Text | Not having much interest or pleasure in doing things. |

### A4 Connectedness
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a4_q1_connectedness | TRUE | Text | Do you have someone to talk to when you have a worry or problem? |

### A5 Gender attitude
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a5_q1_gender_attitude | TRUE | Text | There are times when a woman deserves to be beaten. |
| state_a5_q2_gender_attitude | TRUE | Text | It's a woman's responsibility to avoid getting pregnant. |
| state_a5_q3_gender_attitude | TRUE | Text | A man and a woman should decide together what type of contraceptive to use |
| state_a5_q4_gender_attitude | TRUE | Text | If a guy gets women pregnant, the child is the responsibility of both. |

### A6 Body image
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a6_q1_body_image | TRUE | Text | I feel good about myself. |
| state_a6_q2_body_image | TRUE | Text | I feel good about my body. |

### A7 Self-perceived healthcare
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a2_2_q5_healthcare | TRUE | Text | When I have health needs (like  contraception or flu symptoms), I go to my closest clinic. |
| state_a2_2_q6_healthcare | TRUE | Text | How good a job do you feel you are doing in taking care of your health? |

### A8 Self esteem
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_a2_3_q1_self_esteem | TRUE | Text | I feel that I am a person who has worth — at least as much worth as others. |
| state_a2_3_q2_self_esteem | TRUE | Text | I feel like I have quite a few of good qualities. |
| state_a2_3_q3_self_esteem | TRUE | Text | In general, I tend to feel like a failure. |
| state_a2_3_q4_self_esteem | TRUE | Text | I feel like I don't have much to be proud of. |
| state_a2_3_q5_self_esteem | TRUE | Text | I have a positive attitude toward myself. |
| state_a2_3_q6_self_esteem | TRUE | Text | I'm generally satisfied with myself. |
| state_a2_3_q7_self_esteem | TRUE | Text | I wish I could have more respect for myself. |
| state_a2_3_q8_self_esteem | TRUE | Text | I definitely feel useless at times. |
| state_a2_3_q9_self_esteem | TRUE | Text | Sometimes I think I'm no good at all. |

### Baseline Survey
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_baseline_start | TRUE | Text | Start of Baseline Survey. |
| state_baseline_end | TRUE | Text | End of Baseline Survey. |
| state_self_esteem_assessment_v2 | TRUE | Text | Start of Self Esteem Assessment. |
| state_self_esteem_assessment_v2_end | TRUE | Text | End of of Self Esteem Assessment. |
| state_sexual_health_lit_assessment_v2 | TRUE | Text | Start of SHL Assessment. |
| state_sexual_health_lit_assessment_v2_end | TRUE | Text | End of SHL Assessment. |
| state_self_perceived_healthcare_assessment_v2 | TRUE | Text | Start of SPH Assessment. |
| state_self_perceived_healthcare_assessment_v2_end | TRUE | Text | End of SPH Assessment. |
| state_body_image_assessment_v2 | TRUE | Text | Start of Body Image Assessment in Baseline Survey. |
| state_body_image_assessment_v2_end | TRUE | Text | End of Body Image Assessment in Baseline Survey. |
| state_connectedness_assessment_v2 | TRUE | Text | Start of Connectedness Assessment. |
| state_connectedness_assessment_v2_end | TRUE | Text | End of Connectedness Assessment. |
| state_gender_attitude_assessment_v2 | TRUE | Text | Start of Gender Attitude Assessment. |
| state_gender_attitude_assessment_v2_end | TRUE | Text | End of Gender Attitude Assessment. |
| state_depression_assessment_v2 | TRUE | Text | Start of Depression Assessment. |
| state_depression_assessment_v2_end | TRUE | Text | End of Depression Assessment. |
| state_anxiety_assessment_v2 | TRUE | Text | Start of Anxiety Assessment. |
| state_anxiety_assessment_v2_end | TRUE | Text | End of Anxiety Assessment. |
| state_depression_and_anxiety_v2_end | TRUE | Text | A state to work out a combined score for depression and anxiety. |
| state_sexual_consent_assessment_v2 | TRUE | Text | Start of Sexual Consent Assessment. |
| state_sexual_consent_assessment_v2_end | TRUE | Text | End of Sexual Consent Assessment. |
| state_alcohol_assessment_v2 | TRUE | Text | Start of Alcohol Assessment. |
| state_alcohol_assessment_v2_end | TRUE | Text | End of Alcohol Assessment. |
| state_baseline_halfway_msg | TRUE | Text | Halfway message of baseline survey |
| state_submit_baseline_completed | False | Text | Saves flow results and contact fields relevant to baseline survey end |
| baseline_survey_completed | False | Text | Flag to show end of survey reachedcd  |


### Baseline Sexual Health literacy assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_7_q1_sexual_health_lit | TRUE | Text | People can reduce the risk of getting STIs by |
| baseline_7_q2_sexual_health_lit | TRUE | Text | People can reduce the risk of getting sexual STIs by only having sex with one partner who isn't infected and who has no other partners. |
| baseline_7_q3_sexual_health_lit | TRUE | Text | If I'm sexually active, I am able to insist on using condoms when I have sex. |
| baseline_7_q4_sexual_health_lit | TRUE | Text | My sexual needs or desires are important. |
| baseline_7_q5_sexual_health_lit | TRUE | Text | I think it would be important to focus on my own pleasure as well as my partner's during sexual experiences. |
| baseline_7_q6_sexual_health_lit | TRUE | Text | I expect to enjoy sex. |
| baseline_7_q7_sexual_health_lit | TRUE | Text | The last time you had sex, did you or your partner do or use something to avoid or delay getting pregnant? |
| baseline_7_q8_sexual_health_lit | TRUE | Text | Did you use a condom last time you had penetrative sex? |
| baseline_7_q9_sexual_health_lit | TRUE | Text | What's been the MAIN way you or your partner have tried to delay or avoid getting pregnant? |
| baseline_7_q10A_sexual_health_lit | TRUE | Text | How many sexual partners did you have over the last month? |
| baseline_7_q10B_sexual_health_lit | TRUE | Text | Please tell me how many sexual partners you had in the last month. |
| baseline_7_q11_sexual_health_lit | TRUE | Text | Have you ever been tested for STIs or HIV? |
| baseline_7_q12_sexual_health_lit | TRUE | Text | Are you currently living with HIV? |
| baseline_7_q13_sexual_health_lit | TRUE | Text | Do you take ART (antiretroviral therapy) medication on a regular basis? |
| baseline_7_q14_sexual_health_lit | TRUE | Text | Do you take PrEP (Pre-exposure prophylaxis) medication on a regular basis? |
| state_sexual_health_lit_v2_risk | TRUE | Text | The risk rating for Sexual Health literacy |
| state_sexual_health_lit_v2_score | TRUE | Text | The score for Sexual Health literacy |

### Baseline Self Esteem assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_1_q1_self_esteem | TRUE | Text | I feel that I am a person who has worth |
| baseline_1_q2_self_esteem | TRUE | Text | I feel that I have a number of good qualities. |
| baseline_1_q3_self_esteem | TRUE | Text | All in all, I am inclined to feel that I am a failure. |
| baseline_1_q4_self_esteem | TRUE | Text | I am able to do things as well as most other people. |
| baseline_1_q5_self_esteem | TRUE | Text | I feel I do not have much to be proud of. |
| baseline_1_q6_self_esteem | TRUE | Text | I take a positive attitude toward myself. |
| baseline_1_q7_self_esteem | TRUE | Text | On the whole, I am satisfied with myself. |
| baseline_1_q8_self_esteem | TRUE | Text | I wish I could have more respect for myself. |
| baseline_1_q9_self_esteem | TRUE | Text | I certainly feel useless at times. |
| baseline_1_q10_self_esteem | TRUE | Text | At times I think I am no good at all. |
| state_self_esteem_v2_risk | TRUE | Text | The risk rating for Self Esteem |
| state_self_esteem_v2_score | TRUE | Text | The score for Self Esteem |

### Baseline Connectedness assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_2_q1_connectedness | TRUE | Text | Do you have someone to talk to when you have a worry or problem? |
| state_connectedness_v2_risk | TRUE | Text | The risk rating for Connectedness |
| state_connectedness_v2_score | TRUE | Text | The score for Connectedness |

### Baseline Body Image assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_3_q1_body_image | TRUE | Text | I feel good about myself. |
| baseline_3_q2_body_image | TRUE | Text | I feel good about my body. |
| state_body_image_v2_risk | TRUE | Text | The risk rating for Body Image |
| state_body_image_v2_score | TRUE | Text | The score for Body Image |

### Baseline Depression assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_4_q1_depression | TRUE | Text | Feeling down, depressed or hopeless |
| baseline_4_q2_depression | TRUE | Text | Little interest or pleasure in doing things |
| state_depression_v2_risk | TRUE | Text | The risk rating for Depression |
| state_depression_v2_score | TRUE | Text | The score for Depression |

### Baseline Anxiety assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_5_q1_anxiety | TRUE | Text | Feeling nervous, anxious or on edge |
| baseline_5_q2_anxiety | TRUE | Text | Not being able to stop or control worrying |
| state_anxiety_v2_risk | TRUE | Text | The risk rating for Anxiety |
| state_anxiety_v2_score | TRUE | Text | The score for Anxiety |

### Baseline Depression and Anxiety assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_depression_and_anxiety_v2_risk | TRUE | Text | The risk rating for Depression and Anxiety |
| state_depression_and_anxiety_v2_score | TRUE | Text | The score for Depression and Anxiety |

### Baseline Self Perceived Healthcare assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_6_q1_self_perceived_healthcare | TRUE | Text | How good a job do you feel you are doing in taking care of your health? |
| baseline_6_q2_self_perceived_healthcare | TRUE | Text | In the past 7 days, how many days did you go hungry? |
| baseline_6_q3_self_perceived_healthcare | TRUE | Text | When you have a health need do you go to your closest clinic? |
| state_self_perceived_healthcare_v2_risk | TRUE | Text | The risk rating for Self Perceived Healthcare |
| state_self_perceived_healthcare_v2_score | TRUE | Text | The score for Self Perceived Healthcare |

### Baseline Gender Attitude assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_8_q1_gender_attitude | TRUE | Text | There are times when a woman deserves to be beaten |
| baseline_8_q2_gender_attitude | TRUE | Text | It’s a woman’s responsibility to avoid getting pregnant. |
| baseline_8_q3_gender_attitude | TRUE | Text | A man and a woman should decide together what type of contraceptive to use. |
| baseline_8_q4_gender_attitude | TRUE | Text | If a guy gets a women pregnant, the child is responsibility of both. |
| state_gender_attitude_v2_risk | TRUE | Text | The risk rating for Gender Attitude |
| state_gender_attitude_v2_score | TRUE | Text | The score for Gender Attitude |

### Baseline Sexual Consent assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_9_q1_sexual_consent | TRUE | Text | Robert has the right to force Samantha to have sex. |
| baseline_9_q2_sexual_consent | TRUE | Text | If you're in a relationship, which of these statements describes you best? |
| state_sexual_consent_v2_risk | TRUE | Text | The risk rating for Sexual Consent |
| state_sexual_consent_v2_score | TRUE | Text | The score for Sexual Consent |

### Baseline Alcohol assessment V2
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| baseline_10_q1_alcohol | TRUE | Text | Have you ever felt guilty about drinking or drug use? |
| baseline_10_q2_alcohol | TRUE | Text | Have you ever felt you needed to cut down on your drinking or drug use? |
| baseline_10_q3_alcohol | TRUE | Text | Have people annoyed you by criticising your drinking or drug use? |
| baseline_10_q4_alcohol | TRUE | Text | Have you ever felt you needed a drink or used drugs first thing in the morning (eye‐opener)? |
| state_alcohol_v2_risk | TRUE | Text | The risk rating for Alcohol |
| state_alcohol_v2_score | TRUE | Text | The score for Alcohol |


### Endline Survey
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_endline_start | TRUE | Text | Start of Endline Survey. |
| state_endline_end | TRUE | Text | End of Endline Survey. |
| state_locus_of_control_assessment_endline | True | Text | Starts locus of control Assesment |
| state_locus_of_control_assessment_endline_end | True | Text | End of locus of control Assesment |
| state_self_esteem_assessment_endline | TRUE | Text | Start of Self Esteem Assessment. |
| state_self_esteem_assessment_endline_end | TRUE | Text | End of of Self Esteem Assessment. |
| state_sexual_health_lit_assessment_endline | TRUE | Text | Start of SHL Assessment. |
| state_sexual_health_lit_assessment_endline_end | TRUE | Text | End of SHL Assessment. |
| state_self_perceived_healthcare_assessment_endline | TRUE | Text | Start of SPH Assessment. |
| state_self_perceived_healthcare_assessment_endline_end | TRUE | Text | End of SPH Assessment. |
| state_body_image_assessment_endline | TRUE | Text | Start of Body Image Assessment in Endline Survey. |
| state_body_image_assessment_endline_end | TRUE | Text | End of Body Image Assessment in Endline Survey. |
| state_connectedness_assessment_endline | TRUE | Text | Start of Connectedness Assessment. |
| state_connectedness_assessment_endline_end | TRUE | Text | End of Connectedness Assessment. |
| state_gender_attitude_assessment_endline | TRUE | Text | Start of Gender Attitude Assessment. |
| state_gender_attitude_assessment_endline_end | TRUE | Text | End of Gender Attitude Assessment. |
| state_depression_assessment_endline | TRUE | Text | Start of Depression Assessment. |
| state_depression_assessment_endline_end | TRUE | Text | End of Depression Assessment. |
| state_anxiety_assessment_endline | TRUE | Text | Start of Anxiety Assessment. |
| state_anxiety_assessment_endline_end | TRUE | Text | End of Anxiety Assessment. |
| state_depression_and_anxiety_endline_end | TRUE | Text | A state to work out a combined score for depression and anxiety. |
| state_sexual_consent_assessment_endline | TRUE | Text | Start of Sexual Consent Assessment. |
| state_sexual_consent_assessment_endline_end | TRUE | Text | End of Sexual Consent Assessment. |
| state_alcohol_assessment_endline | TRUE | Text | Start of Alcohol Assessment. |
| state_alcohol_assessment_endline_end | TRUE | Text | End of Alcohol Assessment. |
| state_submit_endline_completed | False | Text | Saves flow results and contact fields relevant to Endline survey end |
| endline_survey_completed | False | Text | Flag to show end of survey reachedcd  |
| state_accept_consent | False | Text | Consent to the endline study |
| state_no_consent | False | Text | No consent to the endline study |
| state_consent | False | Text | Ask for consent to the study |
| state_platform_review_assessment_endline | False | Text | Review the platform |
| state_relationship_status_endline | False | Text | endline relationship status |
| state_submit_terms_and_conditions_endline | False | Text | Endline Terms and Condition Submit |
| state_not_interested | False | Text | Endline Survery not interested |
| state_monthly_household_income_endline | False | Text | Endline household income |
| state_start_terms | False | Text | Endline terms and conditions |
| state_set_reminder_timer | False | Text | Endline terms and conditions reminder |
| state_have_questions | False | Text | Endline I have move questions |

### Endline Sexual Health literacy assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_7_q1_sexual_health_lit | TRUE | Text | People can reduce the risk of getting STIs by |
| endline_7_q2_sexual_health_lit | TRUE | Text | People can reduce the risk of getting sexual STIs by only having sex with one partner who isn't infected and who has no other partners. |
| endline_7_q3_sexual_health_lit | TRUE | Text | If I'm sexually active, I am able to insist on using condoms when I have sex. |
| endline_7_q4_sexual_health_lit | TRUE | Text | My sexual needs or desires are important. |
| endline_7_q5_sexual_health_lit | TRUE | Text | I think it would be important to focus on my own pleasure as well as my partner's during sexual experiences. |
| ednline_7_q6_sexual_health_lit | TRUE | Text | I expect to enjoy sex. |
| endline_7_q7_sexual_health_lit | TRUE | Text | The last time you had sex, did you or your partner do or use something to avoid or delay getting pregnant? |
| endline_7_q8_sexual_health_lit | TRUE | Text | Did you use a condom last time you had penetrative sex? |
| endline_7_q9_sexual_health_lit | TRUE | Text | What's been the MAIN way you or your partner have tried to delay or avoid getting pregnant? |
| endline_7_q10A_sexual_health_lit | TRUE | Text | How many sexual partners did you have over the last month? |
| endline_7_q10B_sexual_health_lit | TRUE | Text | Please tell me how many sexual partners you had in the last month. |
| endline_7_q11_sexual_health_lit | TRUE | Text | Have you ever been tested for STIs or HIV? |
| endline_7_q12_sexual_health_lit | TRUE | Text | Are you currently living with HIV? |
| endline_7_q13_sexual_health_lit | TRUE | Text | Do you take ART (antiretroviral therapy) medication on a regular basis? |
| endline_7_q14_sexual_health_lit | TRUE | Text | Do you take PrEP (Pre-exposure prophylaxis) medication on a regular basis? |
| state_sexual_health_lit_endline_risk | TRUE | Text | The risk rating for Sexual Health literacy |
| state_sexual_health_lit_endline_score | TRUE | Text | The score for Sexual Health literacy |

### Endline LOC assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_1_q1_loc | TRUE | Text | I'm my own boss. |
| endline_1_q2_loc | TRUE | Text | If I work hard, I will be successful. |
| endline_1_q3_loc | TRUE | Text | What I do mainly depends on other people. |
| endline_1_q4_loc | TRUE | Text | Fate often gets in the way of my plans. |
| state_locus_of_control_endline_risk | TRUE | Text | The risk rating for Locus of Control |
| state_locus_of_control_endline_score | TRUE | Text | The score for Locus of Control |

### Endline Self Esteem assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_1_q1_self_esteem | TRUE | Text | I feel that I am a person who has worth |
| endline_1_q2_self_esteem | TRUE | Text | I feel that I have a number of good qualities. |
| endline_1_q3_self_esteem | TRUE | Text | All in all, I am inclined to feel that I am a failure. |
| endline_1_q4_self_esteem | TRUE | Text | I am able to do things as well as most other people. |
| endline_1_q5_self_esteem | TRUE | Text | I feel I do not have much to be proud of. |
| endline_1_q6_self_esteem | TRUE | Text | I take a positive attitude toward myself. |
| endline_1_q7_self_esteem | TRUE | Text | On the whole, I am satisfied with myself. |
| endline_1_q8_self_esteem | TRUE | Text | I wish I could have more respect for myself. |
| endline_1_q9_self_esteem | TRUE | Text | I certainly feel useless at times. |
| endline_1_q10_self_esteem | TRUE | Text | At times I think I am no good at all. |
| state_self_esteem_endline_risk | TRUE | Text | The risk rating for Self Esteem |
| state_self_esteem_endline_score | TRUE | Text | The score for Self Esteem |

### Endline Connectedness assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_2_q1_connectedness | TRUE | Text | Do you have someone to talk to when you have a worry or problem? |
| state_connectedness_endline_risk | TRUE | Text | The risk rating for Connectedness |
| state_connectedness_endline_score | TRUE | Text | The score for Connectedness |

### Endline Body Image assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_3_q1_body_image | TRUE | Text | I feel good about myself. |
| endline_3_q2_body_image | TRUE | Text | I feel good about my body. |
| state_body_image_endline_risk | TRUE | Text | The risk rating for Body Image |
| state_body_image_endline_score | TRUE | Text | The score for Body Image |

### Endline Depression assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_4_q1_depression | TRUE | Text | Feeling down, depressed or hopeless |
| endline_4_q2_depression | TRUE | Text | Little interest or pleasure in doing things |
| state_depression_endline_risk | TRUE | Text | The risk rating for Depression |
| state_depression_endline_score | TRUE | Text | The score for Depression |

### Endline Anxiety assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_5_q1_anxiety | TRUE | Text | Feeling nervous, anxious or on edge |
| endline_5_q2_anxiety | TRUE | Text | Not being able to stop or control worrying |
| state_anxiety_endline_risk | TRUE | Text | The risk rating for Anxiety |
| state_anxiety_endline_score | TRUE | Text | The score for Anxiety |

### Endline Depression and Anxiety assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_depression_and_anxiety_endline_risk | TRUE | Text | The risk rating for Depression and Anxiety |
| state_depression_and_anxiety_endline_score | TRUE | Text | The score for Depression and Anxiety |

### Endline Self Perceived Healthcare assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_6_q1_self_perceived_healthcare | TRUE | Text | How good a job do you feel you are doing in taking care of your health? |
| endline_6_q2_self_perceived_healthcare | TRUE | Text | In the past 7 days, how many days did you go hungry? |
| endline_6_q3_self_perceived_healthcare | TRUE | Text | When you have a health need do you go to your closest clinic? |
| state_self_perceived_healthcare_endline_risk | TRUE | Text | The risk rating for Self Perceived Healthcare |
| state_self_perceived_healthcare_endline_score | TRUE | Text | The score for Self Perceived Healthcare |

### Endline Gender Attitude assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_8_q1_gender_attitude | TRUE | Text | There are times when a woman deserves to be beaten |
| endline_8_q2_gender_attitude | TRUE | Text | It’s a woman’s responsibility to avoid getting pregnant. |
| endline_8_q3_gender_attitude | TRUE | Text | A man and a woman should decide together what type of contraceptive to use. |
| endline_8_q4_gender_attitude | TRUE | Text | If a guy gets a women pregnant, the child is responsibility of both. |
| state_gender_attitude_endline_risk | TRUE | Text | The risk rating for Gender Attitude |
| state_gender_attitude_endline_score | TRUE | Text | The score for Gender Attitude |

### Endline Sexual Consent assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_9_q1_sexual_consent | TRUE | Text | Robert has the right to force Samantha to have sex. |
| endline_9_q2_sexual_consent | TRUE | Text | If you're in a relationship, which of these statements describes you best? |
| state_sexual_consent_endline_risk | TRUE | Text | The risk rating for Sexual Consent |
| state_sexual_consent_endline_score | TRUE | Text | The score for Sexual Consent |

### Endline Alcohol assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_11_q1_alcohol | TRUE | Text | Have you ever felt guilty about drinking or drug use? |
| endline_11_q2_alcohol | TRUE | Text | Have you ever felt you needed to cut down on your drinking or drug use? |
| endline_11_q3_alcohol | TRUE | Text | Have people annoyed you by criticising your drinking or drug use? |
| endline_11_q4_alcohol | TRUE | Text | Have you ever felt you needed a drink or used drugs first thing in the morning (eye‐opener)? |
| state_alcohol_v2_risk | TRUE | Text | The risk rating for Alcohol |
| state_alcohol_v2_score | TRUE | Text | The score for Alcohol |


### Endline Platform Review assessment
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| endline_12_q1_platfor_review | TRUE | Text | Did BWise send you content that related to your sexual needs? |
| endline_12_q2_platfor_review | TRUE | Text | For the content that BWise sent you that related to your needs, was the content that BWise sent you interesting? |
| endline_12_q3_platfor_review | TRUE | Text | How useful did you find the information the BWise sent you for managing your sexual health and relationship needs? |
| endline_12_q4_platfor_review | TRUE | Text | HDid you know BWise is on Facebook and, if so, have you ever visited? |
| endline_12_q5_platfor_review | TRUE | Text | Since joining BWise, have you ever felt like you needed to see a medical service about your mental or sexual health? |
| endline_12_q6_platfor_review | TRUE | Text | Did you know you can use BWise WA to find a clinic for you based on your needs? |
| endline_12_q7_platfor_review | TRUE | Text | Did you ever go to one of the services that BWise recommended? |
| endline_12_q8_platfor_review | TRUE | Text | Since joining BWise, have you ever felt like you needed to speak to a counsellor about your mental or sexual health? |
| endline_12_q9_platfor_review | TRUE | Text | Did you know you can request a callback from a LoveLife counsellor through the B-Wise WhatsApp chatbot? |


## EJAF Location Survey
| state_name | accepts_user_input | data_type | description |
| ---------- | ------------------ | --------- | ----------- |
| state_location_introduction | TRUE | Text | Surveu introduction
| state_location_not_invited | TRUE | Text | Tells user they weren't invited to the study
| state_location_already_completed | TRUE | Text | Tells user they already completed the study
| state_location_province | TRUE | Text | Ask user which province they live in
| state_location_not_recruiting | FALSE | Text | Tells user we're not recruiting in the province they live in
| state_location_name_city | TRUE | Text | Ask user the name of the city they live in
| state_location_area_type | TRUE | Text | Ask user the area type they live in
| state_location_group_invite | TRUE | Text | Invite user to group discussions
| state_location_update_status | FALSE | Text | Updates ejaf_location_survey_status contact field on rapidpro
| state_location_end | TRUE | Text | Tells user the survey is over with some prompts to go to different places
| state_location_question | TRUE | text | Asks user if they'd like to continue after seeing consent pdf
| state_send_consent_pdf | FALSE | text | Send the consent pdf to the user
| state_location_decline | FALSE | text | Tells users there are no consequences for not joining study
| state_location_update_invalid_province | FALSE | text | Updates the ejaf_location_survey_status contact field on rapidpro
| state_location_invalid_province | FALSE | text | Tells them they are not eligible for the survey
