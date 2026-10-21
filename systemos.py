import os
import sys
import ctypes
import subprocess

def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_command(command):
    """Helper function to run system commands safely."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        # Combine stdout and stderr as Windows tools sometimes route errors to stdout
        error_msg = (e.stderr or "") + (e.stdout or "")
        return False, error_msg

def sync_system_time():
    """Starts the Windows Time service and forces a clock synchronization."""
    print("Checking Windows Time Service (w32time)...")
    
    # 1. Ensure the Windows Time service is running
    # 'net start w32time' returns exit code 0 if started, or 2914 if already running
    subprocess.run(["net", "start", "w32time"], capture_output=True)

    print("Attempting to resynchronize system clock...")
    
    # 2. Trigger the resync
    success, output = run_command(["w32tm", "/resync"])
    
    if success:
        print("\n[SUCCESS] Time synchronized successfully!")
        print(output.strip())
    else:
        print("\n[ERROR] Failed to synchronize time.")
        print(f"Windows Error Details:\n{output.strip()}")
        
        # Check for a common background service issue
        if "The service has not been started" in output:
            print("\nSuggestion: Try forcing a service reset in an Admin CMD using:")
            print("w32tm /register")

if __name__ == "__main__":
    # Automatically elevate privileges if not running as Administrator
    if not is_admin():
        print("Requesting Administrator privileges...")
        # Re-run the script passing the same arguments with administrative rights
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception as e:
            print(f"Failed to elevate permissions: {e}")
        sys.exit(0)

    # If already admin, run the sync function
    sync_system_time()
    
    # Keep window open if it auto-elevated into a new prompt window
    input("\nPress Enter to exit...")



# import subprocess
# import sys

# def sync_system_time():
#     """Triggers the Windows Time Service to resynchronize the clock."""
#     try:
#         # Run the w32tm resync command
#         result = subprocess.run(
#             ["w32tm", "/resync"], 
#             capture_output=True, 
#             text=True, 
#             check=True
#         )
#         print("Success:")
#         print(result.stdout)
#     except subprocess.CalledProcessError as e:
#         print("Failed to sync time. Make sure you are running this script as Administrator.")
#         print(e.stderr)

# if __name__ == "__main__":
#     sync_system_time()
