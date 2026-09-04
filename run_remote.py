import time
import sys

def main():
    print("MOCK RUN: Sleeping for 120 seconds to simulate Colab pipeline...", flush=True)
    for i in range(120):
        if i % 10 == 0:
            print(f"Mock progress: {i}/120 seconds elapsed", flush=True)
        time.sleep(1)
    print("MOCK RUN: Finished successfully.", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
