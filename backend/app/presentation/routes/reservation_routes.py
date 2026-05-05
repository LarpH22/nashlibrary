from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.reservation_controller import ReservationController
from ..middlewares.auth_middleware import set_current_user


reservation_bp = Blueprint("reservation", __name__)
controller = ReservationController()


@reservation_bp.route("/", methods=["POST"])
@jwt_required()
def create_reservation():
    return controller.create_reservation(set_current_user())


@reservation_bp.route("/student", methods=["GET"])
@jwt_required()
def list_student_reservations():
    return controller.list_student_reservations(set_current_user())


@reservation_bp.route("/<int:reservation_id>", methods=["DELETE"])
@jwt_required()
def cancel_student_reservation(reservation_id):
    return controller.cancel_student_reservation(reservation_id, set_current_user())


@reservation_bp.route("/", methods=["GET"])
@jwt_required()
def list_all_reservations():
    return controller.list_all_reservations(set_current_user())


@reservation_bp.route("/<int:reservation_id>/approve", methods=["POST"])
@jwt_required()
def approve_reservation(reservation_id):
    return controller.approve_reservation(reservation_id, set_current_user())


@reservation_bp.route("/<int:reservation_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_reservation(reservation_id):
    return controller.cancel_reservation(reservation_id, set_current_user())


@reservation_bp.route("/<int:reservation_id>/claim", methods=["POST"])
@jwt_required()
def mark_claimed(reservation_id):
    return controller.mark_claimed(reservation_id, set_current_user())


@reservation_bp.route("/expire", methods=["POST"])
@jwt_required()
def expire_reservations():
    return controller.expire_reservations(set_current_user())
