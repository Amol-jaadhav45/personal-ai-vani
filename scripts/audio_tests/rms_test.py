import sounddevice as sd
import numpy as np

def run():
    print("Listening (say something!)...")
    with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
        for i in range(20):
            chunk, _ = stream.read(1024)
            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            print(f"Chunk {i} RMS:", rms)

if __name__ == '__main__':
    run()
