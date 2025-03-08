import time
import subprocess

def run_script(script_name):
    """Runs a given script using subprocess."""
    print(f"Running {script_name}...")
    subprocess.run(["python3", script_name])

def main():
    # Cycle through the four scripts
    run_script("led_red.py")    # Red for 5 seconds
    time.sleep(5)

    run_script("led_green.py")  # Green for 5 seconds
    time.sleep(5)

    run_script("led_blue.py")   # Blue for 5 seconds
    time.sleep(5)

    run_script("led_rainbow.py")  # Rainbow for 5 seconds
    time.sleep(5)

    # Run the rainbow cycle indefinitely
    print("Starting indefinite rainbow cycle...")
    run_script("led_rainbow.py")

if __name__ == "__main__":
    main()
