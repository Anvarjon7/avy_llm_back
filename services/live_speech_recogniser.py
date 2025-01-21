import speech_recognition as sr

r = sr.Recognizer()


def listen_to_user():
    with sr.Microphone() as source:
        print("Say something(max waiting time is 7s)...")
        try:
            # Listen for the full 7 seconds of audio
            audio_text = r.record(source, duration=7)

            # Recognize speech using Google API
            query = r.recognize_google(audio_text)
            print("Text: " + query)
            return query
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
