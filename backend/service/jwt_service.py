import os

from backend.errors.access_error import InvalidTokenError, UnauthorizedError


# I could make JWT token verification class, using JOSE, but for demonstration purposes I simplified
# Also, there would be a token provider
# The tokens would have several verifications, including emitter, expiration time, scope, among others
class JWTService(object):
    def __init__(self):
        self.__token = os.getenv("ACCESS_TOKEN")

    def verify_header(self, auth_header: str) -> bool:
        auth_type = auth_header.split(" ")[0]
        if auth_type != "Bearer":
            raise InvalidTokenError()

        try:
            auth_token = auth_header.split(" ")[1]
        except IndexError:
            raise InvalidTokenError()

        if auth_token != self.__token:
            raise UnauthorizedError()

        return True
