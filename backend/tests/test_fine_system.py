import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

from backend.app.infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl
from backend.app.presentation.controllers.fine_controller import FineController
from backend.app.presentation.routes import fine_routes


class FakeFineService:
    def __init__(self, states=None, fines=None):
        self.states = states or {}
        self.fines = fines or []

    def calculate_fine(self, loan_id):
        return self.states[loan_id].get('payable_amount', 0)

    def pay_fine(self, loan_id):
        if self.states[loan_id].get('pay_result') is False:
            return None
        return {'loan_id': loan_id, 'total_paid': self.states[loan_id].get('payable_amount', 0), 'fines': []}

    def get_fine_state_for_loan(self, loan_id):
        return self.states.get(loan_id)

    def list_student_fines(self, student_id):
        return list(self.fines)


class UseCaseProxy:
    def __init__(self, callback):
        self.callback = callback

    def execute(self, loan_id):
        return self.callback(loan_id)


class FineControllerTest(unittest.TestCase):
    def make_controller(self, states=None, fines=None):
        controller = FineController()
        service = FakeFineService(states=states, fines=fines)
        controller.fine_service = service
        controller.calculate_fine_use_case = UseCaseProxy(service.calculate_fine)
        controller.pay_fine_use_case = UseCaseProxy(service.pay_fine)
        return controller

    def make_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_calculate_rejects_invalid_loan_id(self):
        app = self.make_app()
        controller = self.make_controller()
        with app.test_request_context('/fines/calculate?loan_id=abc'):
            response, status = controller.calculate_fine()
        self.assertEqual(status, 400)
        self.assertEqual(response.get_json()['message'], 'loan_id must be a valid integer')

    def test_calculate_returns_loan_not_found(self):
        app = self.make_app()
        controller = self.make_controller(states={})
        with app.test_request_context('/fines/calculate?loan_id=404'):
            response, status = controller.calculate_fine()
        self.assertEqual(status, 404)
        self.assertEqual(response.get_json()['message'], 'Loan not found')

    def test_pay_returns_fine_already_paid(self):
        app = self.make_app()
        controller = self.make_controller(states={7: {'status': 'paid', 'payable_amount': 0}})
        with app.test_request_context('/fines/pay', method='POST', json={'loan_id': 7}):
            response, status = controller.pay_fine()
        self.assertEqual(status, 409)
        self.assertEqual(response.get_json()['message'], 'Fine already paid')

    def test_pay_returns_no_fine_exists(self):
        app = self.make_app()
        controller = self.make_controller(states={8: {'status': 'no_fine', 'payable_amount': 0}})
        with app.test_request_context('/fines/pay', method='POST', json={'loan_id': 8}):
            response, status = controller.pay_fine()
        self.assertEqual(status, 404)
        self.assertEqual(response.get_json()['message'], 'No fine exists for this loan')

    def test_student_fine_history_summary_includes_paid_and_unpaid(self):
        app = self.make_app()
        controller = self.make_controller(fines=[
            {'amount': 3.0, 'status': 'unpaid'},
            {'amount': 2.0, 'status': 'paid'},
        ])
        with app.test_request_context('/api/fines/student'):
            response, status = controller.list_student_fines({'role': 'student', 'student_id': 12})
        data = response.get_json()
        self.assertEqual(status, 200)
        self.assertEqual(data['summary']['total_unpaid'], 3.0)
        self.assertEqual(data['summary']['total_paid'], 2.0)
        self.assertEqual(len(data['fines']), 2)


class FineRouteIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.original_controller = fine_routes.controller
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        JWTManager(self.app)
        self.app.register_blueprint(fine_routes.fine_bp, url_prefix='/api/fines')
        with self.app.app_context():
            self.token = create_access_token(
                identity='student@example.com',
                additional_claims={'role': 'student', 'student_id': 44},
            )

    def tearDown(self):
        fine_routes.controller = self.original_controller

    def auth_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_calculate_endpoint_calls_controller(self):
        class Controller:
            def calculate_fine(self):
                return jsonify({'loan_id': 5, 'fine_amount': 4.0}), 200

        fine_routes.controller = Controller()
        response = self.app.test_client().get('/api/fines/calculate?loan_id=5', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['fine_amount'], 4.0)

    def test_pay_endpoint_calls_controller(self):
        class Controller:
            def pay_fine(self):
                return jsonify({'message': 'Fine paid'}), 200

        fine_routes.controller = Controller()
        response = self.app.test_client().post('/api/fines/pay', json={'loan_id': 5}, headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['message'], 'Fine paid')

    def test_student_history_endpoint_passes_current_student(self):
        class Controller:
            def list_student_fines(self, current_user):
                return jsonify({'student_id': current_user['student_id'], 'fines': []}), 200

        fine_routes.controller = Controller()
        response = self.app.test_client().get('/api/fines/student', headers=self.auth_headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['student_id'], 44)


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.lastrowid = 22
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        query = self.queries[-1][0]
        if 'COUNT(*) AS fine_count' in query:
            return {'fine_count': 0}
        if 'FROM borrow_records' in query:
            return {
                'borrow_id': 3,
                'student_id': 9,
                'due_date': date.today() - timedelta(days=4),
                'return_date': None,
            }
        if 'WHERE fine_id=%s' in query:
            return {
                'fine_id': 22,
                'borrow_id': 3,
                'student_id': 9,
                'amount': 4.0,
                'reason': 'Overdue book fine',
                'status': 'paid',
                'issued_date': date.today(),
                'paid_date': date.today(),
            }
        return None

    def fetchall(self):
        query = self.queries[-1][0]
        if "status IN ('unpaid', 'pending')" in query and 'FOR UPDATE' in query:
            return []
        return []


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeCloseLoanCursor(FakeCursor):
    def fetchone(self):
        query = self.queries[-1][0]
        if 'FROM borrow_records' in query and 'FOR UPDATE' in query:
            return {
                'borrow_id': 10,
                'student_id': 4,
                'book_id': 2,
                'copy_id': 6,
                'due_date': date(2026, 5, 1),
                'return_date': None,
                'status': 'active',
            }
        if 'SELECT 1 FROM fines' in query:
            return None
        if 'SELECT * FROM borrow_records' in query:
            return {
                'borrow_id': 10,
                'student_id': 4,
                'book_id': 2,
                'copy_id': 6,
                'due_date': date(2026, 5, 1),
                'return_date': date(2026, 5, 5),
                'status': 'returned',
            }
        return None


class FakeCloseLoanConnection(FakeConnection):
    def __init__(self):
        self.cursor_instance = FakeCloseLoanCursor()
        self.committed = False
        self.rolled_back = False


class LoanRepositoryFineLogicTest(unittest.TestCase):
    def test_fine_calculation_uses_overdue_days_times_rate(self):
        repo = LoanRepositoryImpl()
        due_date = date(2026, 5, 1)
        returned_at = datetime(2026, 5, 4, 9, 0)
        self.assertEqual(repo._compute_fine(due_date, returned_at), 3.0)
        self.assertEqual(repo._compute_days_overdue(due_date, returned_at), 3)

    def test_pay_fine_creates_paid_record_for_computed_overdue_fine(self):
        fake_conn = FakeConnection()
        with patch('backend.app.infrastructure.repositories_impl.loan_repository_impl.get_connection', return_value=fake_conn):
            result = LoanRepositoryImpl().pay_fine(3)

        self.assertTrue(fake_conn.committed)
        self.assertEqual(result['loan_id'], 3)
        self.assertEqual(result['total_paid'], 4.0)
        joined_queries = '\n'.join(query for query, _ in fake_conn.cursor_instance.queries)
        self.assertIn('INSERT INTO fines', joined_queries)

    def test_close_loan_generates_unpaid_fine_for_overdue_return(self):
        fake_conn = FakeCloseLoanConnection()
        with patch('backend.app.infrastructure.repositories_impl.loan_repository_impl.get_connection', return_value=fake_conn), \
             patch('backend.app.infrastructure.repositories_impl.loan_repository_impl.ensure_inventory_schema'):
            result = LoanRepositoryImpl().close_loan(10, datetime(2026, 5, 5, 8, 30), student_id=4)

        self.assertTrue(fake_conn.committed)
        self.assertEqual(result['fine_amount'], 4.0)
        joined_queries = '\n'.join(query for query, _ in fake_conn.cursor_instance.queries)
        self.assertIn("VALUES (%s, %s, %s, %s, 'unpaid', %s)", joined_queries)



if __name__ == '__main__':
    unittest.main()
