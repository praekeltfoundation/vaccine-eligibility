Introduction
------------

For any contact fields that we need to store permanently, we store these in RapidPro. There is a `rapidpro.py` module which has helper methods for updating contact fields in RapidPro.

On every inbound message, we fetch these contact fields, and store them in `self.user.metadata`. So you should not use the `get_profile` method, rather used the fields cached in `self.user.metadata`. The `update_profile` method in `rapidpro.py` also updates the field in `self.user.metadata` to ensure that they stay in sync.

Fields
------

| Field name                                 | use                                                                                                     |
|--------------------------------------------|---------------------------------------------------------------------------------------------------------|
| assessment_reminder                        | Set a time to remind the user to take an assessment that they haven't started                           |
| assessment_name                            | Name of the assessment we need to remind the user to take                                               |
| sexual_health_lit_risk                     | save the risk status from sexual_health_lit assessment (high_risk or low_risk)                          |
| sexual_health_lit_score                    | save the score from sexual_health_lit assessment                                                        |
