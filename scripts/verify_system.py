import subprocess
import sys
import os

def run_verification():
    print("Starting System Verification...")
    
    # Check if we are in the root directory
    if not os.path.exists("tests"):
        print("Error: 'tests' directory not found. Please run this script from the project root.")
        sys.exit(1)
        
    # Run pytest
    print("\n[1/2] Running Unit Tests...")
    # Using 'uv run pytest' if available or just 'pytest'
    # Assuming the user or agent will run this with the correct python environment
    
    cmd = [sys.executable, "-m", "pytest", "tests/unit", "-v"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Unit Tests Passed")
        else:
            print("❌ Unit Tests Failed")
            print(result.stderr)
            sys.exit(result.returncode)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

    print("\n[2/2] Checking Dependencies...")
    try:
        # Check standard imports
        import fastapi
        import sqlalchemy
        import ocpp
        print("✅ Core dependencies loadable")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        sys.exit(1)
        
    print("\n🎉 System Verification Successful!")

if __name__ == "__main__":
    run_verification()
