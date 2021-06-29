We should have some sort of keyword state, that can map keywords to labels. eg. '1' or 'yes' should be labelled 'yes'. This can then be our default state type for most things, and we only use the ChoiceState for dynamic choice lists. This will help simplify things with formatting (eg. if you want the numbers to be bolded on whatsapp), and allow for easier integration into a CMS.

`next` could be a dictionary as a shortcut to map labels to states names (could also allow functions that return state names as values), which could replace MenuStates
