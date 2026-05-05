from flask import jsonify, request

from ...infrastructure.repositories_impl.reservation_repository_impl import ReservationRepositoryImpl


class ReservationController:
    def __init__(self):
        self.repository = ReservationRepositoryImpl()

    def _parse_pagination_params(self):
        page = request.args.get('page', type=int)
        limit = request.args.get('limit', type=int)
        paginate = page is not None or limit is not None
        page = page if page and page > 0 else 1
        limit = limit if limit and limit > 0 else 15
        offset = (page - 1) * limit
        return page, limit, offset, paginate

    def create_reservation(self, current_user=None):
        if not current_user:
            return jsonify({"message": "Authentication required"}), 401
        if current_user.get("role") != "student":
            return jsonify({"message": "Only students can reserve books"}), 403

        data = request.get_json(silent=True) or {}
        book_id = data.get("book_id")
        if not book_id:
            return jsonify({"message": "Book ID is required"}), 400

        try:
            reservation = self.repository.create_reservation(int(current_user.get("student_id")), int(book_id))
            if reservation.get("status") == "ready":
                message = "Reservation approved. The book is ready for pickup and expires within 48 hours."
            elif int(reservation.get("queue_position") or 0) > 1:
                message = f"Reservation saved. You joined the queue at position {reservation.get('queue_position')}."
            else:
                message = "Reservation saved. You are first in the queue."
            return jsonify({
                "message": message,
                "reservation": reservation,
            }), 201
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 409
        except Exception:
            return jsonify({"message": "Unable to create reservation. Please try again."}), 500

    def list_student_reservations(self, current_user=None):
        if not current_user:
            return jsonify({"message": "Authentication required"}), 401
        if current_user.get("role") != "student":
            return jsonify({"message": "Student access required"}), 403

        page, limit, offset, paginate = self._parse_pagination_params()
        result = self.repository.list_student_reservations(int(current_user.get("student_id")), limit=limit if paginate else None, offset=offset if paginate else None)
        if paginate and isinstance(result, dict):
            return jsonify(result)
        return jsonify({"reservations": result})

    def cancel_student_reservation(self, reservation_id, current_user=None):
        if not current_user:
            return jsonify({"message": "Authentication required"}), 401
        if current_user.get("role") != "student":
            return jsonify({"message": "Student access required"}), 403

        reservation = self.repository.cancel_reservation(
            int(reservation_id),
            student_id=int(current_user.get("student_id")),
        )
        if not reservation:
            return jsonify({"message": "Reservation not found or already closed."}), 404
        return jsonify({"message": "Reservation cancelled.", "reservation": reservation})

    def list_all_reservations(self, current_user=None):
        if not self._can_manage(current_user):
            return jsonify({"message": "Admin or librarian access required"}), 403

        page, limit, offset, paginate = self._parse_pagination_params()
        status = request.args.get("status")
        result = self.repository.list_all_reservations(status=status, limit=limit if paginate else None, offset=offset if paginate else None)
        if paginate and isinstance(result, dict):
            return jsonify(result)
        return jsonify({"reservations": result})

    def approve_reservation(self, reservation_id, current_user=None):
        if not self._can_manage(current_user):
            return jsonify({"message": "Admin or librarian access required"}), 403

        reservation = self.repository.approve_reservation(int(reservation_id), self._actor_id(current_user))
        if not reservation:
            return jsonify({"message": "Active reservation not found."}), 404

        message = reservation.get("message") or "Reservation is ready for pickup."
        return jsonify({"message": message, "reservation": reservation})

    def cancel_reservation(self, reservation_id, current_user=None):
        if not self._can_manage(current_user):
            return jsonify({"message": "Admin or librarian access required"}), 403

        reservation = self.repository.cancel_reservation(int(reservation_id))
        if not reservation:
            return jsonify({"message": "Reservation not found or already closed."}), 404
        return jsonify({"message": "Reservation cancelled.", "reservation": reservation})

    def mark_claimed(self, reservation_id, current_user=None):
        if not self._can_manage(current_user):
            return jsonify({"message": "Admin or librarian access required"}), 403

        try:
            result = self.repository.mark_claimed(int(reservation_id), self._actor_id(current_user))
            if not result:
                return jsonify({"message": "Ready reservation not found."}), 404
            return jsonify({"message": "Reserved book marked as claimed.", **result})
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 409

    def expire_reservations(self, current_user=None):
        if not self._can_manage(current_user):
            return jsonify({"message": "Admin or librarian access required"}), 403

        count = self.repository.expire_reservations()
        return jsonify({"message": "Expired reservations removed.", "expired_count": count})

    def _can_manage(self, current_user):
        return bool(current_user and current_user.get("role") in ["admin", "librarian"])

    def _actor_id(self, current_user):
        return (
            current_user.get("admin_id")
            or current_user.get("librarian_id")
            or current_user.get("user_id")
        )
