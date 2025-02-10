import speech_recognition as sr

recognizer = sr.Recognizer()

def extract_text_from_audio(filename):
    """Extracts text from the recorded audio file."""

    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print("Extracted Text:", text)
        return text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
