import subprocess
import sys
import time
import os
from pathlib import Path

def check_dependencies():
    try:
        import fastapi
        import streamlit
        import langchain
        import openai
        print("All dependencies are installed")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_configuration():
    if not Path(".env").exists():
        print(".env file not found. Please create one with your configuration.")
        print("Example .env file:")
        print("OPENAI_API_KEY=your_openai_api_key_here")
        print("CALENDAR_ID=your_calendar_id_here")
        return False
 
    if not Path("credentials/service_account.json").exists():
        print("Google Calendar service account file not found.")
        print("Please place your service_account.json file in the credentials/ directory.")
        return False
    
    print("Configuration looks good")
    return True

def start_backend():
    print("Starting FastAPI backend server...")
    try:
        original_dir = os.getcwd()
        
        os.chdir("backend")
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])
        
        print("Backend server started on http://localhost:8000")
        return process, original_dir
        
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return None, None

def start_frontend():
    print("Starting Streamlit frontend...")
    try:

        os.chdir("frontend")
        

        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501"
        ])
        
        print("Frontend started on http://localhost:8501")
        return process
        
    except Exception as e:
        print(f"Failed to start frontend: {e}")
        return None

def main():
    print("Calendar Booking Agent Startup")
    print("=" * 40)

    if not check_dependencies():
        return

    if not check_configuration():
        print("\nPlease fix the configuration issues above and try again.")
        return
    
    print("\nStarting Calendar Booking Agent...")
    
    backend_process, original_dir = start_backend()
    if not backend_process:
        return
    
    time.sleep(3)
    
    if original_dir:
        os.chdir(original_dir)

    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    print("\nCalendar Booking Agent is running!")
    print("Frontend: http://localhost:8501")
    print("Backend API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop both servers")
    
    try:
        
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("Servers stopped")

if __name__ == "__main__":
    main() 