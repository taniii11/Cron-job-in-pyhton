import subprocess
from concurrent.futures import ThreadPoolExecutor

scripts = ["fetch_speed_test.py", "fetch_router_list.py", "fetch_health.py"]

def run_script(script):
    try:
        subprocess.run(["python", script], check=True)
        print(f"{script} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while executing {script}: {e}")
    
def main():
    with ThreadPoolExecutor() as executor:
        executor.map(run_script, scripts)

if __name__ == "__main__":
    main()
