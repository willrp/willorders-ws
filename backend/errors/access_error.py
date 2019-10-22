from .error import Error


class AccessError(Error):
    def __init__(self, message):
        self.__message = message

    def __str__(self):
        return self.__message


class InvalidTokenError(AccessError):
    def __init__(self):
        super().__init__("Invalid token")


class UnauthorizedError(AccessError):
    def __init__(self):
        super().__init__("Unauthorized")
