import speech_recognition as sr
import webbrowser
import pyttsx3
import musiclibrary
import time
import requests
import threading
import queue
from client import GEMINI_API_KEY
import google.generativeai as genai
import vlc
import yt_dlp

player = None
music_playing = False


def play_song_online(song_name):
    global player, music_playing

    # Stop current song if playing
    if player and music_playing:
        player.stop()

    speak(f"Playing {song_name}")

    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song_name, download=False)
        audio_url = info['entries'][0]['url']

    instance = vlc.Instance('--no-video')
    player = instance.media_player_new()
    media = instance.media_new(audio_url)
    player.set_media(media)

    player.audio_set_volume(80)
    player.play()

    music_playing = True


genai.configure(api_key="AIzaSyD5vr5-YkZlIy5s6IQlVP5LuNG8yauJK3U")
# Thread-safe queue for storing commands
command_queue = queue.Queue()

def ask_gemini(prompt):
    """Send prompt to Google Gemini and return response"""
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini Exception:", e)
        return None

recognizer = sr.Recognizer()
newsapi = "a77d51081cd54f55b5a673808dcdd6b7"

# ✅ Initialize TTS engine ONCE globally
engine = pyttsx3.init('sapi5')
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# Function to initialize TTS engine
def init_tts():
    try:
        engine = pyttsx3.init('sapi5')  # Explicitly use SAPI5 on Windows
        engine.setProperty('rate', 150)  # Slower speech
        engine.setProperty('volume', 1.0)  # Max volume
        voices = engine.getProperty('voices')
        if not voices:
            print("No voices available. Check SAPI5 installation.")
            return None
        print("Available voices:")
        for i, voice in enumerate(voices):
            print(f"Voice {i}: {voice.name}")
        engine.setProperty('voice', voices[0].id)  # Set first available voice
        return engine
    except Exception as e:
        print(f"Failed to initialize TTS engine: {e}")
        return None

# Function to make Jarvis speak
def speak(text):
    try:
        # engine = init_tts()  # Reinitialize for each speak
        if not engine:
            print("TTS engine not initialized.")
            return
        print(f"Attempting to speak: {text}")
        engine.say(text)
        engine.runAndWait()
        print(f"Successfully spoke: {text}")
    except Exception as e:
        print(f"Error in speak: {e}")
    finally:
        time.sleep(1.5)  # Increased pause to avoid audio conflicts

def processCommand(c):
    try:
        print(f"Processing command: '{c}'")
        if any(phrase in c.lower() for phrase in ["open google", "google"]):
            speak("Opening Google")
            print("Attempting to open Google...")
            webbrowser.open("https://google.com")
            print("Google opened successfully")
        # elif "play" in c.lower():
        #   song = c.lower().replace("play", "").strip()
        #   if song:
        #      play_song_online(song)
        elif c.lower().startswith("play"):
               song = c.lower().split(" ")[1]
               link = musiclibrary.music[song]
               webbrowser.open(link)

        elif any(phrase in c.lower() for phrase in ["open brave", "brave"]):
            speak("Opening Brave")
            print("Attempting to open Brave...")
            webbrowser.open("https://brave.com")
            print("Brave opened successfully")
        elif any(phrase in c.lower() for phrase in ["open youtube", "youtube"]):
            speak("Opening YouTube")
            print("Attempting to open YouTube...")
            webbrowser.open("https://youtube.com")
            print("YouTube opened successfully")
        elif any(phrase in c.lower() for phrase in ["open perplexity", "perplexity"]):
            speak("Opening Perplexity")
            print("Attempting to open Perplexity...")
            webbrowser.open("https://perplexity.com")
            print("Perplexity opened successfully")
        elif c.lower().startswith("play"):
            try:
                song = c.lower().split(" ")[1]
                link = musiclibrary.music[song]
                speak(f"Playing {song}")
                print(f"Attempting to play {song}...")
                webbrowser.open(link)
                print(f"{song} opened successfully")
            except KeyError:
                speak(f"Sorry, I couldn't find the song {song}")
                print(f"Song {song} not found in musiclibrary")
        elif "news" in c.lower():
            speak("Fetching the latest news")
            print("Fetching news...")
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get('articles', [])
                for i, article in enumerate(articles[:3]):  # Limit to 3 articles
                    speak(f"News {i+1}: {article['title']}")
            else:
                speak("Sorry, I couldn't fetch the news")
                print(f"News API request failed: {r.status_code}")
        elif "thanks" in c.lower():
            speak("You're welcome, bro!")
            print("Responded to thanks")
        else:
            # 🔥 If no known command matched, send it to Gemini
            speak("Let me think...")
            ai_reply = ask_gemini(c)
            speak(ai_reply)
            if ai_reply:
             speak(ai_reply)
            else:
              speak("Sorry, I am having trouble connecting to my brain.")
    except Exception as e:
        print(f"Error in processCommand: {e}")
        speak("An error occurred while processing the command")
    finally:
        if music_playing and player:
           player.audio_set_volume(80)

def listen():
    """Background thread to continuously listen"""
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            word = recognizer.recognize_google(audio)
            print(f"You said: {word}")
            command_queue.put(word)
        except Exception:
            # Ignore timeouts and recognition errors to keep loop running
            pass


if __name__ == "__main__":
    listener_thread = threading.Thread(target=listen, daemon=True)
    listener_thread.start()

    speak("Initializing Jarvis...")

    while True:
        try:
            if not command_queue.empty():
                word = command_queue.get()
                text = word.lower()
                
                if any(phrase in word.lower() for phrase in ["good night", "go to bed", "have sweet dreams jarvis"]):
                    speak("Good night, sleep well!")
                    break
                elif any(phrase in word.lower() for phrase in ["hello jarvis", "hi jarvis", "hey jarvis","jarvis"]):
                    speak("Yes sir, at your service")
                elif any(phrase in word.lower() for phrase in ["good morning jarvis" , "jarvis good morning"]):
                    speak("Good morning bro! How can I help you?")
                elif "jarvis" in text and len(text.split()) <= 3:
                    if music_playing and player:
                       player.audio_set_volume(20)  # lower volume
                       speak("Yes sir, at your service")
                else:
                    command = word.lower().replace("jarvis", "").strip()
                    if command:
                        processCommand(command)
                    else:
                        print("No command detected.")
            time.sleep(0.1)  # Prevent CPU overuse
        except KeyboardInterrupt:
            speak("Shutting down. Goodbye!")
            break


    # listener_thread = threading.Thread(target=listen, daemon=True)
    # listener_thread.start()

    # speak("Initializing Jarvis...")
    # while True:
    #     try:
    #         with sr.Microphone() as source:
    #             print("Listening...")
    #             recognizer.adjust_for_ambient_noise(source, duration=0.5)
    #             audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    #         word = recognizer.recognize_google(audio)
    #         print(f"You said: {word}")

    #         # Process commands with or without "Jarvis"
    #         if any(phrase in word.lower() for phrase in ["hello jarvis", "hi jarvis", "hey jarvis","jarvis"]):
    #             print("Detected greeting")
    #             speak("Yes sir, at your service")
    #         if any(phrase in word.lower() for phrase in ["good morning jarvis" , "jarvis good morning"]):
    #             # print("Detected greeting")
    #             speak("good morning bro! how can i help you")
    #         elif any(phrase in word.lower() for phrase in ["good night", "go to bed", "have sweet dreams jarvis"]):
    #             print("Detected exit command")
    #             speak("Good night, sleep well!")
    #             break
    #         else:
    #             command = word.lower().replace("jarvis", "").strip()
    #             print(f"Extracted command: '{command}'")
    #             if command:
    #                 processCommand(command)
    #             else:
    #                 print("No command detected, waiting for input")

    #     except Exception as e:
    #       print(f"Error: {e}")
            # Avoid speak in exception to prevent TTS overload






























# # import speech_recognition as sr
# # import webbrowser
# # import pyttsx3
# # import musiclibrary
# # import time
# # import requests
# # # from gtts import gTTS
# # # import os

# # recognizer = sr.Recognizer()
# # engine = pyttsx3.init(driverName='sapi5')  # Force Windows Speech API
# # engine.setProperty('rate', 150)  # slower speech
# # engine.setProperty('volume', 1.0)
# # newsapi = "a77d51081cd54f55b5a673808dcdd6b7"

# # def speak(text):
# #     engine.say(text)
# #     engine.runAndWait()
# #     time.sleep(0.3)


# # def processCommand(c):
# #     if "open google" in c.lower():
# #         webbrowser.open("https://google.com")
# #     elif "open brave" in c.lower():
# #         webbrowser.open("https://brave.com")
# #     elif "open youtube" in c.lower():
# #         webbrowser.open("https://youtube.com")
# #     elif "open perplexity" in c.lower():
# #         webbrowser.open("https://perplexity.com")
# #     elif c.lower().startswith("play"):
# #         song = c.lower().split(" ")[1]
# #         link = musiclibrary.music[song]
# #         webbrowser.open(link)
# #     elif "news" in c.lower():
# #         r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")

# #         if r.status_code == 200:
# #             data = r.json()
# #             articles = data.get('articles',[])

# #             for article in articles:
# #                 speak(article['title'])




# # if __name__=="__main__":
# #     speak("Say hi jarvis to initalize the command")
# #     while True:
# #        # Listen for the wake word "Jarvis"
# #        # obtain audio from the microphone
# #         r = sr.Recognizer()

# #         print("recognizing...")
# #         try:
# #             engine = pyttsx3.init(driverName='sapi5')
# #             with sr.Microphone() as source:
# #                 print("Listening....")
# #                 audio = r.listen(source, timeout=5, phrase_time_limit=3)
# #             word = r.recognize_google(audio)
# #             print(f"You said: {word}")
# #             if "jarvis" in word.lower():
# #                 print("Detected Jarvis! Now speaking 'Yaa'...")
# #                 speak("Yes Sir")
# #                 time.sleep(1)
# #                 # Listen for command
# #                 with sr.Microphone() as source:
# #                     print("jarvis Active...")
# #                     audio = r.listen(source)
# #                     command = r.recognize_google(audio)
# #                     print(f"DEBUG: Google heard -> {command}")


# #                     processCommand(command)



# #         except Exception as e:
# #             print("Error; {0}".format(e))