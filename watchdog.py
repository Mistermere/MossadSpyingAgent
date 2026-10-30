import subprocess
import os
import sys

def main():
    # Get the folder where the apps are located
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    tracker_path = os.path.join(base_path, "Tracker.exe")
    tabwise_path = os.path.join(base_path, "Tabwise.exe")

    # 1. Start the Tracker completely detached
    if os.path.exists(tracker_path):
        subprocess.Popen([tracker_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

    # 2. Start the UI
    if os.path.exists(tabwise_path):
        subprocess.Popen([tabwise_path])

if __name__ == "__main__":
    main()