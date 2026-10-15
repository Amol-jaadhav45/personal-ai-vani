import sounddevice as sd
import numpy as np

def test_sd():
    print("Testing sounddevice...")
    print(f"Default devices: {sd.default.device}")
    
    # Just read 1 chunk
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
        chunk, _ = stream.read(1024)
        rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
        print(f"RMS of first chunk: {rms}")
        print("Success.")

if __name__ == "__main__":
    test_sd()
