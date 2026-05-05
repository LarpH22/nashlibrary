import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing date conversion in loan repository")
print("=" * 60)

try:
    from backend.app.infrastructure.repositories_impl.loan_repository_impl import LoanRepositoryImpl
    
    print("\n✓ LoanRepositoryImpl imported")
    
    repo = LoanRepositoryImpl()
    print("✓ Repository instance created")
    
    # Test querying loans
    print("\nTesting find_loans_by_student_id(1)...")
    loans = repo.find_loans_by_student_id(1)
    print(f"✓ Query executed, got {len(loans)} loans")
    
    if loans:
        print("\nFirst loan data:")
        for key, value in loans[0].items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        # Test JSON serialization
        print("\nTesting JSON serialization...")
        import json
        try:
            json_str = json.dumps(loans)
            print(f"✓ JSON serialization successful")
            print(f"  JSON preview: {json_str[:200]}")
        except TypeError as e:
            print(f"✗ JSON serialization failed: {e}")
    else:
        print("No loans found (this is OK if there's no data)")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
