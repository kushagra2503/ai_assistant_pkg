"""
Speech recognition utility for the AI Assistant.
"""

import speech_recognition as sr
import logging

logger = logging.getLogger("ai_assistant")

def listen_for_speech():
    """
    Listen for speech input from the microphone.
    
    Returns:
        str: Recognized speech text or None if not recognized
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        
        try:
            # Listen for audio input
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio)
            
            # Improve GitHub term recognition
            text = text.replace("get hub", "github")
            text = text.replace("get have", "github")
            text = text.replace("good hub", "github")
            text = text.replace("repository", "repository")
            text = text.replace("repo", "repo")
            
            return text
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            print("\n❌ Could not request results from speech recognition service.")
            return None
        except Exception as e:
            print(f"\n❌ Speech recognition error: {e}")
            return None
