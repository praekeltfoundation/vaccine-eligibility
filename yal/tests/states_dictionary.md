
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


### Onboarding flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_persona_name                         |        TRUE        |     Text     |            TRUE          | Asks user to enter a custom name for the bot                                                              |
| state_save_persona_name                    |        FALSE       |              |            TRUE          | Updates user profile with the new name                                                                         |
| state_persona_emoji                        |        TRUE        |     Text     |            TRUE          | Asks user to enter an emoji to represent the bot                                                           |
| state_save_persona_emoji                   |        FALSE       |              |            FALSE         | Updates user profile with the new emoji                                                                        |
| state_profile_intro                        |        FALSE       |              |            FALSE         | Sends a message to thank and set expectations                                                                 |
| state_age                                  |        TRUE        |     Int      |            TRUE          | Asks user to enter their age                                                                                  |
| state_gender                               |        TRUE        |     Text     |            TRUE          | Asks user to enter their gender. User response is "female", "male", "non_binary", "other" or "rather_not_say" |
| state_other_gender                         |        TRUE        |     Text     |            TRUE          | Asks user to enter their gender using free text                                                               |
| state_submit_onboarding                    |        FALSE       |     Text     |            TRUE          | Adds onboarding choices to user profile                                                                      |
| state_onboarding_complete                  |        FALSE       |              |            TRUE          | Redirects user to AAQ start state in case they want to ask a question                                      |
| state_stop_onboarding_reminders            |        TRUE        |     Text     |            TRUE          | Resets fields used for onboarding reminders                                                                 |
| state_reschedule_onboarding_reminders      |        TRUE        |     Text     |            TRUE          | Sets onboarding reminder fields so that reminder is resent later                                              |
| state_handle_onboarding_reminder_response  |        TRUE        |     Text     |            TRUE          | Routes user to other state based on their reponse to the onboarding reminder                              |


### OptOut flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_optout                               |        TRUE        |     Text     |            TRUE          | Asks the user what they would to do. User response is "stop notifications", "delete saved" or "skip"     |
| state_submit_optout                        |        FALSE       |              |            FALSE         | Resets fields used for reminders so any pending reminders are cancelled                                 |
| state_stop_notifications                   |        FALSE       |              |            TRUE          | Sends user a message and then routes them to state_optout_survey                                          |
| state_optout_survey                        |        TRUE        |     Text     |            TRUE          | Asks user why they opted out. User repsonse is chosen from a list                                         |
| state_delete_saved                         |        TRUE        |     Text     |            TRUE          | Deletes profile data. User response is "see" to see the cleaned profile                                |
| state_tell_us_more                         |        TRUE        |     Text     |            TRUE          | Asks user why they opted out. User repsonse is freeText                                                   |
| state_farewell_optout                      |        FALSE       |              |            FALSE         | Bids the user farewell and closes the session                                                           |


### Quiz flow
| state_name                                 | accepts_user_input |   data_type  | added_to_flow_results_app | description                                                                      |
|--------------------------------------------|--------------------|--------------|---------------------------|---------------------------------------------------------------------------------|
| state_quiz_start                           |        FALSE       |              |            TRUE          | Resets session info about user's progress through quiz                                                     |
| state_quiz_question                        |        TRUE        |     Text     |            TRUE          | Sends the requested quiz question to the user. User response can be "callme", "menu", "redo" or others    |
| state_quiz_process_answer                  |        TRUE        |     Text     |            TRUE          | Processes the user's response to the quiz question and updates their score                            |
| state_quiz_answer_feedback                 |        TRUE        |     Text     |            TRUE          | Sends user feedback about their answer and a button to proceed to the next question                        |
