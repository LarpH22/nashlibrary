import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
try:
    from app.presentation.routes.loan_routes import loan_bp, controller
    print(f'Successfully imported loan_bp: {loan_bp}')
    print(f'Successfully imported controller: {controller}')
except Exception as e:
    import traceback
    print(f'Import error: {e}')
    traceback.print_exc()
