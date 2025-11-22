import sys
import time
print("Starting import test...")
start = time.time()
try:
    import whisper
    print(f"Import successful in {time.time() - start:.2f} seconds")
except Exception as e:
    print(f"Import failed: {e}")
