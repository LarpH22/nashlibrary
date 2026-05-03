import os
import sys
import traceback
from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..controllers.loan_controller import LoanController
from ..middlewares.auth_middleware import set_current_user

loan_bp = Blueprint('loan', __name__)
controller = LoanController()

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'loan_route_debug.log'))

def log_loan_route(message, extra=None):
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as file:
            file.write(f"[{message}] {extra if extra is not None else ''}\n")
    except Exception:
        pass


@loan_bp.route('/student', methods=['GET'], strict_slashes=False)
@jwt_required()
def list_student_loans():
    log_loan_route('route', 'Route function called')
    try:
        current_user = set_current_user()
        log_loan_route('current_user', repr(current_user))
        result = controller.list_student_loans(current_user)
        log_loan_route('result', repr(result))
        return result
    except Exception as e:
        log_loan_route('exception', f"{type(e).__name__}: {str(e)}")
        try:
            with open(LOG_PATH, 'a', encoding='utf-8') as file:
                traceback.print_exc(file=file)
        except Exception:
            pass
        raise
