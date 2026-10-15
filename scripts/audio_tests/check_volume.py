import sounddevice as sd
import numpy as np
import time

def check_volume():
    print("Speak into your microphone loudly for 3 seconds...")
    max_rms = 0
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1024) as stream:
        for _ in range(50): # ~3 seconds
            chunk, _ = stream.read(1024)
            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            if rms > max_rms:
                max_rms = rms
    # Also test float32
    max_float = 0
    with sd.InputStream(samplerate=16000, channels=1, dtype='float32', blocksize=1024) as stream:
        for _ in range(50):
            chunk, _ = stream.read(1024)
            rms = float(np.sqrt(np.mean(chunk**2)))
            if rms > max_float: max_float = rms
            
    print(f"Max RMS (int16): {max_rms}")
    print(f"Max RMS (float32): {max_float}")

if __name__ == "__main__":
    check_volume()
