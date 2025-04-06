# Core functionality for language learning application
import speech_recognition as sr
import requests
import time
from gtts import gTTS
import os
import unicodedata
import threading
from functools import partial

# API configuration
API_KEY = "86dd78dd-1b69-451c-a701-773312d7bfc8:fx"  # Set your DeepL API key here
API_URL = "https://api-free.deepl.com/v2/translate"

def translate_text(text, target_language):
    """
    Translate text to the target language using the DeepL API.
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (e.g., 'ES', 'FR')
        
    Returns:
        str: Translated text or error message
    """
    # Check if API key is set
    api_key = API_KEY
    
    if not api_key:
        print("Error: DeepL API key is not configured.")
        return "[Translation Error: API key not configured.]"
    
    params = {
        'auth_key': api_key,
        'text': text,
        'target_lang': target_language
    }
    
    try:
        response = requests.post(API_URL, data=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'translations' in data and len(data['translations']) > 0:
            return data['translations'][0]['text']
        else:
            print(f"Unexpected API response format: {data}")
            return "[Translation Error: Unexpected API response format]"
            
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return f"[Translation Error: {str(e)}]"
    except Exception as e:
        print(f"General error: {e}")
        return f"[Error: {str(e)}]"

def capture_user_voice(language="en-US"):
    """
    Capture the user's voice and return the text.
    
    Args:
        language (str): Language code for speech recognition
        
    Returns:
        str or None: Recognized text or None if recognition failed
    """
    recognizer = sr.Recognizer()
    
    # Configure recognition parameters
    recognizer.pause_threshold = 2.0
    recognizer.dynamic_energy_threshold = True
    
    with sr.Microphone() as source:
        print(f"Listening for {language} speech...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        
        try:
            audio = recognizer.listen(
                source,
                timeout=None,
                phrase_time_limit=None
            )
            print("Processing speech...")
        except sr.WaitTimeoutError:
            print("No speech detected")
            return None

    try:
        user_text = recognizer.recognize_google(
            audio, 
            language=language
        )
        print(f"Recognized: {user_text}")
        return user_text
    except sr.UnknownValueError:
        print("Could not understand speech")
        return None
    except sr.RequestError as e:
        print(f"Recognition error: {e}")
        return None

def play_audio(text, language, debug=True):
    """
    Convert text to speech and play it.
    
    Args:
        text (str): Text to speak
        language (str): Language code (e.g., 'es', 'fr')
        debug (bool): Whether to print debug info
    """
    import os
    import tempfile
    import time
    
    if debug:
        print(f"Speaking in {language}: {text[:30]}{'...' if len(text) > 30 else ''}")
    
    temp_filename = None
    
    try:
        # Create temp file
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, f"speech_{int(time.time())}.mp3")
        
        # Generate speech
        tts = gTTS(text=text, lang=language)
        tts.save(temp_filename)
        time.sleep(0.5)  # Wait for file to be ready
        
        # Play audio with appropriate player for the platform
        if os.name == 'posix':  # Linux/Mac
            os.system(f"mpg123 -q {temp_filename}")
        else:  # Windows
            try:
                # Try using pygame
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.quit()
            except Exception as e:
                print(f"Pygame error: {e}")
                # Fall back to playsound with blocking mode (more reliable)
                try:
                    import playsound
                    playsound.playsound(temp_filename, True)
                except Exception as e:
                    print(f"Audio playback error: {e}")
                    
    except Exception as e:
        print(f"Error generating or playing audio: {e}")
    finally:
        # Clean up temp file
        if temp_filename and os.path.exists(temp_filename):
            try:
                time.sleep(1.0)  # Give time for file to be released
                os.remove(temp_filename)
            except Exception as e:
                print(f"Error removing temp file: {e}")

def normalize_text(text):
    """
    Normalize text by removing accents and converting to lowercase.
    
    Args:
        text (str): Text to normalize
        
    Returns:
        str: Normalized text
    """
    if text is None:
        return None
    # Convert to lowercase and normalize accents
    normalized = unicodedata.normalize('NFKD', text.lower())
    # Remove accents
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    return normalized

def run_in_thread(callback=None):
    """
    Decorator to run a function in a separate thread.
    
    Args:
        callback (callable): Function to call with the result
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if callback:
                def thread_target():
                    result = func(*args, **kwargs)
                    callback(result)
                threading.Thread(target=thread_target).start()
                return None
            else:
                threading.Thread(target=partial(func, *args, **kwargs)).start()
                return None
        return wrapper
    return decorator

def test_functionality():
    """Simple test of core functionality without UI"""
    print("=== Language Learning Core Functionality Test ===")
    print("1. Testing Speech Recognition")
    user_text = capture_user_voice()
    
    if not user_text:
        print("Speech recognition failed. Using sample text instead.")
        user_text = "Hello, how are you today?"
    
    print("\n2. Testing Translation")
    target_language = input("Enter target language code (ES, FR, DE, IT, JA): ").strip().upper() or "ES"
    translated_text = translate_text(user_text, target_language)
    print(f"Original: {user_text}")
    print(f"Translated ({target_language}): {translated_text}")
    
    print("\n3. Testing Text-to-Speech")
    play_audio(translated_text, target_language.lower())
    
    print("\n4. Testing Text Normalization")
    print(f"Original: {translated_text}")
    print(f"Normalized: {normalize_text(translated_text)}")
    
    print("\nAll tests complete!")

if __name__ == "__main__":
    test_functionality()
