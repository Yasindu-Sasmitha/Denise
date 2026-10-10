import speech_recognition as sr

print("🎤 Testing microphone...")
r = sr.Recognizer()
try:
    with sr.Microphone() as source:
        print("✅ Microphone opened! Say something in 3 seconds...")
        audio = r.listen(source, timeout=3, phrase_time_limit=3)
        print("🎤 Audio captured! Transcribing...")
        text = r.recognize_google(audio)
        print(f"✅ You said: {text}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()