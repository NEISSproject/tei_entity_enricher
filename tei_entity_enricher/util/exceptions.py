# todo: get caller with inspect module?


class MissingDefinition(Exception):
    def __init__(
        self,
        missing_parameter: str,
        caller_class: str,
        caller_method: str,
        message: str = "{} {}: parameter {} has not been defined (correctly)",
    ):
        self.missing_parameter = missing_parameter
        self.caller_class: str = caller_class
        self.caller_method: str = caller_method
        self.message: str = message
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.caller_class, self.caller_method, self.missing_parameter)


class BadFormat(Exception):
    def __init__(
        self,
        filepath: str,
        caller_class: str,
        caller_method: str,
        message: str = "{} {}: file or data from {} in bad format",
    ):
        self.filepath: str = filepath
        self.caller_class: str = caller_class
        self.caller_method: str = caller_method
        self.message: str = message
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.caller_class, self.caller_method, self.filepath)


class FileNotFound(Exception):
    def __init__(
        self,
        filepath: str,
        caller_class: str,
        caller_method: str,
        message: str = "{} {}: file or data from {} not found",
    ):
        self.filepath = filepath
        self.caller_class: str = caller_class
        self.caller_method: str = caller_method
        self.message: str = message
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.caller_class, self.caller_method, self.filepath)


class FileNotFoundOrBadFormat(Exception):
    def __init__(
        self,
        filepath: str,
        caller_class: str,
        caller_method: str,
        message: str = "{} {}: file or data from {} not found or in bad format",
    ):
        self.filepath = filepath
        self.caller_class: str = caller_class
        self.caller_method: str = caller_method
        self.message: str = message
        super().__init__(self.message)

    def __str__(self):
        return self.message.format(self.caller_class, self.caller_method, self.filepath)
