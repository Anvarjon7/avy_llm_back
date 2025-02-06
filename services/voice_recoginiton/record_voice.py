import sounddevice as sd
import numpy as np
import wave

def record_voice(filename, duration=5, sample_rate=16000):
    print(f"Recording... Speak for {duration} seconds.")

    audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    print(f"Voice sample saved as {filename}")
