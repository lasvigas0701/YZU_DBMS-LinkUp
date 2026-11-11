import subprocess
import sys
import time

scripts = [
    "setup.py",     
    "fix_data.py",  
    "fix_chat.py"   
]

print("init database and fix data process started...\n")

for script in scripts:
    try:

        subprocess.run([sys.executable, script], check=True)
        print(f"{script} successfully executed.\n")
        time.sleep(1)
        
    except subprocess.CalledProcessError:
        print(f"\n Error executing {script}.")
        break
    except Exception as e:
        print(f"\n An unexpected error: {e}")
        break