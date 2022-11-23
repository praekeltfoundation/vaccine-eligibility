
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
| state_aaq_start                            |        TRUE        |     Text     |            TRUE           | Asks user to enter a question                                                                      |
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
| state_aaq_timeout_unrecognised_option      |        TRUE        |     Text     |            TRUE           | Offers user options when we didn't recognise feedback response                                         |
