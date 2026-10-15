import speech_recognition as sr

def test_mic():
    print("Testing mic via SpeechRecognition...")
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Listening for 5 seconds...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("Processing audio...")
            text = recognizer.recognize_google(audio)
            print(f"I heard: {text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mic()
