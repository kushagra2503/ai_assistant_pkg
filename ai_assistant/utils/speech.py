"""
Speech recognition utility for the AI Assistant.
"""

import speech_recognition as sr
import logging

logger = logging.getLogger("ai_assistant")

def listen_for_speech():
    """
    Listen for speech input from the microphone and convert to text.
    
    Returns:
        str or None: Recognized text or None if recognition failed
    """
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    try:
        with microphone as source:
            print("🎤 Speak now...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            prompt = recognizer.recognize_google(audio, language="en")
            print(f"🗣 You said: {prompt}")
            return prompt
        except sr.UnknownValueError:
            print("❌ Speech not recognized. Try again.")
            return None
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            print(f"❌ Error in speech recognition: {e}")
            return None
    except Exception as e:
        logger.error(f"Microphone error: {e}")
        print(f"❌ Error accessing microphone: {e}")
        return None
