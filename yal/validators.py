from vaccine.states import ErrorMessage


def day_validator(error_text):
    async def validator(value):
        if value != "skip":
            if value is None or value.strip() == "":
                raise ErrorMessage(error_text)
            if int(value) > 31:
                raise ErrorMessage(error_text)

    return validator
