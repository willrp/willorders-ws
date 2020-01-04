from flask_restplus import Namespace, Resource

from backend.service import OrderService
from backend.util.response.error import ErrorResponse
from backend.controller import ErrorHandler, auth_required


deleteNS = Namespace("Order", description="Order related operations.")

ERRORMODEL = ErrorResponse.get_model(deleteNS, "ErrorResponse")


@deleteNS.route("/delete/<string:user_slug>/<string:order_slug>", strict_slashes=False)
class DeleteController(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__orderservice = OrderService()

    @auth_required()
    @deleteNS.doc(security=["token"])
    @deleteNS.param("user_slug", description="User slug", _in="path", required=True)
    @deleteNS.param("order_slug", description="Order slug", _in="path", required=True)
    @deleteNS.response(200, description="Deleted with success", mask=False)
    @deleteNS.response(400, "Bad Request", ERRORMODEL)
    @deleteNS.response(401, "Unauthorized", ERRORMODEL)
    @deleteNS.response(404, "Not Found", ERRORMODEL)
    @deleteNS.response(500, "Unexpected Error", ERRORMODEL)
    @deleteNS.response(504, "No response from gateway server", ERRORMODEL)
    def delete(self, user_slug, order_slug):
        """Order delete."""
        try:
            self.__orderservice.delete(user_slug=user_slug, order_slug=order_slug)
            return {}, 200
        except Exception as error:
            return ErrorHandler(error).handle_error()
