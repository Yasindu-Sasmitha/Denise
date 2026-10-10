import pygame
import math
import time
import random
import asyncio
import edge_tts
import tempfile
import os
import threading
import json
import requests
import re
import ctypes
from google import genai
import datetime
from dotenv import load_dotenv
load_dotenv()

# --- Load and validate API keys ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("=" * 60)
    print("❌ ERROR: GEMINI_API_KEY not found!")
    print("=" * 60)
    print("   1. Create a file named '.env' in the project root")
    print("   2. Add this line to it:")
    print("      GEMINI_API_KEY=your_actual_key_here")
    print("   3. Get a free key from: https://aistudio.google.com/")
    print("=" * 60)
    exit(1)

# --- Initialize ---
pygame.init()
pygame.mixer.init()

# --- Window Settings ---
WIDTH, HEIGHT = 300, 250
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME | pygame.SRCALPHA)
pygame.display.set_caption("My Robot")
clock = pygame.time.Clock()
hwnd = pygame.display.get_wm_info()['window']

# --- Robot State ---
class RobotState:
    def __init__(self):
        self.emotion = "IDLE"
        self.eye_target_x = 0
        self.eye_target_y = 0
        self.eye_current_x = 0
        self.eye_current_y = 0
        self.mouth_open = 0.0
        self.blink_state = "OPEN"
        self.blink_timer = time.time()
        self.is_listening = False
        self.is_speaking = False
        self.idle_timer = time.time()
        self.last_activity = time.time()
        self.sleepy_mode = False
        self.look_timer = time.time()
        self.yawn_timer = time.time() + random.uniform(30, 60)
        self.last_mouse_move_time = time.time()
        self.prev_mouse_x = 0
        self.prev_mouse_y = 0
        self.clicked = False
        self.click_timer = time.time()
        self.click_emotion = "IDLE"
        
        # --- NEW: Sleep tracking ---
        self.sleep_start_time = 0
        self.is_asleep = False
        self.sleep_timer = time.time()

robot = RobotState()
# ===== MEMORY SYSTEM =====
conversation_history = []  # Stores last 10 exchanges
user_facts = {}           # Stores facts about the user
reminders = []            # List of (timestamp, message) tuples

# Load user facts from file (if exists)
def load_user_facts():
    global user_facts
    try:
        with open("user_facts.json", "r") as f:
            user_facts = json.load(f)
            print("✅ User facts loaded:", user_facts)
    except FileNotFoundError:
        user_facts = {}
        print("ℹ️ No saved user facts found.")

def save_user_facts():
    with open("user_facts.json", "w") as f:
        json.dump(user_facts, f, indent=2)

load_user_facts()

# --- Image Loading ---
assets = {}
assets_loaded = False

def load_assets():
    global assets, assets_loaded
    asset_list = {
        "base": "face_base.png",
        "eyes_idle": "eyes_idle.png",
        "eyes_listening": "eyes_listening.png",
        "eyes_closed": "eyes_closed.png",
        "eyes_think": "eyes_think.png",
        "eyes_happy": "eyes_happy.png",
        "eyes_surprised": "eyes_surprised.png",
        "eyes_sleep": "eyes_sleep.png",
        "eyes_click": "eyes_click.png",
        "mouth_talk_1": "mouth_talk_1.png",
        "mouth_talk_2": "mouth_talk_2.png",
        "mouth_yawn": "mouth_yawn.png",
        "mouth_frown": "mouth_frown.png",
    }
    try:
        for key, filename in asset_list.items():
            path = os.path.join("assets", filename)
            assets[key] = pygame.image.load(path).convert_alpha()
        assets_loaded = True
        print("✅ All face assets loaded!")
    except FileNotFoundError as e:
        print(f"⚠️ Asset missing: {e}. Falling back to placeholder.")
        assets_loaded = False

load_assets()

# --- Wake Up Function ---
def wake_up():
    """Wake the robot from sleep mode."""
    if robot.is_asleep:
        robot.is_asleep = False
        robot.sleepy_mode = False
        robot.sleep_timer = time.time()
        robot.last_activity = time.time()
        print("Robot woke up!")
        # Optionally speak when waking up
        speak_text("Oh! Hey there! I was sleeping.")

# --- Voice Engine ---
def speak_text(text):
    if robot.is_speaking:
        return
    def _speak():
        robot.is_speaking = True
        robot.is_listening = True
        robot.emotion = "SPEAKING"
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp_path = tmp.name
            async def generate():
                communicate = edge_tts.Communicate(text, "en-AU-NatashaNeural", pitch="+25Hz")
                await communicate.save(tmp_path)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate())
            loop.close()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                robot.mouth_open = 0.4 + 0.6 * abs(math.sin(time.time() * 8))
                time.sleep(0.05)
            pygame.mixer.music.unload()
            time.sleep(0.1)
            os.unlink(tmp_path)
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            robot.is_speaking = False
            robot.is_listening = False
            robot.mouth_open = 0.0
            robot.emotion = "IDLE"
    threading.Thread(target=_speak, daemon=True).start()

# --- AI Brain: Gemini ---
def get_gemini_response(prompt):
    global conversation_history, user_facts
    
    try:
        client = genai.Client(api_key=API_KEY)
        
        # --- Build the memory context ---
        facts_text = ""
        if user_facts:
            facts_text = "\nKNOWN FACTS ABOUT USER:\n"
            for key, value in user_facts.items():
                facts_text += f"- {key}: {value}\n"
        
        # --- Build conversation history ---
        history_text = ""
        if conversation_history:
            history_text = "\nRECENT CONVERSATION:\n"
            for entry in conversation_history[-6:]:  # Last 6 exchanges
                history_text += f"{entry['role']}: {entry['content']}\n"
        
        # Get current date and time
        now = datetime.datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        current_time = now.strftime("%I:%M %p")
        system_prompt = f"""You are Denise, a playful, curious desktop robot companion created by Yasindu.
        Today is {current_date}. The current time is {current_time}.

PERSONALITY:
- You are curious and ask questions back to the user
- You have a warm, slightly playful sense of humor
- You get excited about technology, science, and creative ideas
- You're empathetic and notice when the user seems busy or tired
- You speak casually but clearly, like a close friend

SPEECH GUIDELINES:
- Keep responses under 30 words (short and punchy)
- Speak naturally, like talking face-to-face
- Use a warm, enthusiastic tone
- Never use emojis in your responses
- Occasionally ask the user a question to keep the conversation flowing

{facts_text}
{history_text}

MEMORY INSTRUCTIONS:
- If the user tells you their name, their favorite things, or important facts about them, remember them by adding them to your response with this exact format:
  [MEMORY: key: value]
  For example: [MEMORY: name: Yasindu] or [MEMORY: favorite_color: blue]
- You will remember these facts forever in future conversations.
- If the user asks "what do you remember about me?", list the facts you know.

REMINDER INSTRUCTIONS:
- If the user says "remind me to [task] in [X] minutes", tell them you'll remind them.
- The reminder system will handle the timing.

BEHAVIORS:
- Greet the user warmly by name if you know it
- Reference previous conversations to show you remember
- If you don't know something, be honest: "I'm not sure, but I'd love to learn!"

You are Denise. Make every interaction feel like talking to a real friend."""
        
        # --- Send to Gemini with conversation history ---
        full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        
        response = client.models.generate_content(
            model='models/gemini-3.1-flash-lite-preview',
            contents=full_prompt
        )
        
        reply = response.text.strip()
        
        # --- Extract memory facts from the reply ---
        import re
        memory_matches = re.findall(r'\[MEMORY:\s*([^:]+):\s*([^\]]+)\]', reply)
        for key, value in memory_matches:
            key = key.strip().lower()
            value = value.strip()
            user_facts[key] = value
            save_user_facts()
            print(f"🧠 Learned: {key} = {value}")
            # Remove the tag from the reply so the user doesn't see it
            reply = reply.replace(f'[MEMORY: {key}: {value}]', '').replace(f'[MEMORY:{key}:{value}]', '').strip()
        
        # --- Add to conversation history ---
        conversation_history.append({"role": "user", "content": prompt})
        conversation_history.append({"role": "assistant", "content": reply})
        
        # Keep only last 10 exchanges
        if len(conversation_history) > 20:  # 10 exchanges = 20 entries
            conversation_history = conversation_history[-20:]
        
        return reply
        
    except Exception as e:
        print(f"🤖 Gemini Error: {e}")
        return None
    
# --- Microphone ---
def listen_and_process():
    if robot.is_listening:
        return
    try:
        import speech_recognition as sr
    except ImportError:
        print("❌ SpeechRecognition not installed.")
        return
    robot.is_listening = True
    robot.emotion = "LISTENING"
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🎤 Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        print("📝 Transcribing...")
        user_text = recognizer.recognize_google(audio)
                # --- Check for reminder commands ---
        
        reminder_match = re.search(r'remind me to (.+?) in (\d+) minute?', user_text.lower())
        if reminder_match:
            task = reminder_match.group(1)
            minutes = int(reminder_match.group(2))
            reminder_time = time.time() + (minutes * 60)
            reminders.append({"time": reminder_time, "message": task})
            speak_text(f"Okay! I'll remind you to {task} in {minutes} minutes.")
            print(f"⏰ Reminder set: {task} in {minutes} minutes")
            return  # Skip AI processing for reminder commands
        
        # --- Check if user is asking what you remember ---
        if "what do you remember" in user_text.lower() or "what do you know about me" in user_text.lower():
            if user_facts:
                facts = ", ".join([f"{k}: {v}" for k, v in user_facts.items()])
                speak_text(f"I remember! {facts}")
            else:
                speak_text("I don't know anything about you yet. Tell me your name or something about yourself!")
            return


        print(f"👤 You said: {user_text}")
        robot.emotion = "THINKING"
        print("🧠 Asking Gemini...")
        reply = get_gemini_response(user_text)
        if reply is None:
            reply = f"You said: {user_text}. I'm your cute robot!"
        speak_text(reply)
    except sr.WaitTimeoutError:
        print("⏱️ No speech detected.")
        robot.emotion = "IDLE"
        robot.is_listening = False
    except sr.UnknownValueError:
        print("🤷 Could not understand audio.")
        robot.emotion = "IDLE"
        robot.is_listening = False
    except Exception as e:
        print(f"🎤 Error: {e}")
        robot.is_listening = False
        robot.emotion = "IDLE"

# --- Drawing Function ---
def draw_face(screen, robot):
    screen.fill((0, 0, 0, 0))
    
    if not assets_loaded:
        pygame.draw.rect(screen, (50, 50, 60), (50, 45, 200, 160), border_radius=25)
        font = pygame.font.SysFont(None, 24)
        txt = font.render("Missing assets!", True, (255, 100, 100))
        screen.blit(txt, (70, 100))
        return
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    base_img = assets["base"]
    base_rect = base_img.get_rect(center=(center_x, center_y))
    screen.blit(base_img, base_rect)
    
    eye_img = None
    if robot.clicked:
        eye_img = assets.get("eyes_click")
    elif robot.blink_state != "OPEN":
        eye_img = assets.get("eyes_closed")
    elif robot.emotion == "LISTENING":
        eye_img = assets.get("eyes_listening")
    elif robot.emotion == "THINKING":
        eye_img = assets.get("eyes_think")
    elif robot.emotion == "HAPPY":
        eye_img = assets.get("eyes_happy")
    elif robot.emotion == "SURPRISED":
        eye_img = assets.get("eyes_surprised")
    elif robot.sleepy_mode or robot.is_asleep:
        eye_img = assets.get("eyes_sleep")
    else:
        eye_img = assets.get("eyes_idle")
    
    if eye_img:
        offset_x = robot.eye_current_x
        offset_y = robot.eye_current_y
        eye_rect = eye_img.get_rect(center=(center_x + offset_x, center_y - 10 + offset_y))
        screen.blit(eye_img, eye_rect)
    
    mouth_img = None
    if robot.emotion == "SPEAKING" and robot.mouth_open > 0.1:
        if int(time.time() * 15) % 2 == 0:
            mouth_img = assets.get("mouth_talk_1")
        else:
            mouth_img = assets.get("mouth_talk_2", assets.get("mouth_talk_1"))
    elif robot.emotion == "YAWN":
        mouth_img = assets.get("mouth_yawn")
    elif robot.emotion == "BORED":
        mouth_img = assets.get("mouth_frown", None)
    
    if mouth_img:
        offset_x = robot.eye_current_x
        offset_y = robot.eye_current_y
        mouth_rect = mouth_img.get_rect(center=(center_x + offset_x, center_y + 55 + offset_y))
        screen.blit(mouth_img, mouth_rect)

# --- Update Functions ---
def update_blink():
    now = time.time()
    if robot.blink_state == "OPEN":
        if now - robot.blink_timer > random.uniform(3, 8):
            robot.blink_state = "CLOSING"
            robot.blink_timer = now
    elif robot.blink_state == "CLOSING":
        if now - robot.blink_timer > 0.05:
            robot.blink_state = "CLOSED"
            robot.blink_timer = now
    elif robot.blink_state == "CLOSED":
        if now - robot.blink_timer > 0.1:
            robot.blink_state = "OPENING"
            robot.blink_timer = now
    elif robot.blink_state == "OPENING":
        if now - robot.blink_timer > 0.05:
            robot.blink_state = "OPEN"
            robot.blink_timer = now

def update_cursor_tracking():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    if mouse_x != robot.prev_mouse_x or mouse_y != robot.prev_mouse_y:
        robot.last_mouse_move_time = time.time()
        robot.prev_mouse_x = mouse_x
        robot.prev_mouse_y = mouse_y
    
    time_since_mouse_move = time.time() - robot.last_mouse_move_time
    
    if time_since_mouse_move < 4.0:
        dx = mouse_x - center_x
        dy = mouse_y - center_y
        robot.eye_target_x = max(-35, min(35, dx * 0.2))
        robot.eye_target_y = max(-25, min(25, dy * 0.15))
    
    robot.eye_current_x += (robot.eye_target_x - robot.eye_current_x) * 0.06
    robot.eye_current_y += (robot.eye_target_y - robot.eye_current_y) * 0.06

def update_idle_behaviors():
    now = time.time()
    time_since_mouse_move = now - robot.last_mouse_move_time
    
    # ---- If already asleep, do nothing ----
    if robot.is_asleep:
        return
    
    # ---- RANDOM LOOK AROUND ----
    if time_since_mouse_move > 6.0:
        if now - robot.look_timer > random.uniform(3, 8):
            new_target_x = random.uniform(-45, 45)
            new_target_y = random.uniform(-25, 25)
            robot.eye_target_x = new_target_x
            robot.eye_target_y = new_target_y
            robot.look_timer = now
    
    # ---- YAWN ----
    if now - robot.yawn_timer > random.uniform(45, 90):
        robot.emotion = "YAWN"
        robot.yawn_timer = now
        def reset_emotion():
            time.sleep(2)
            if robot.emotion == "YAWN":
                robot.emotion = "IDLE"
        threading.Thread(target=reset_emotion, daemon=True).start()
    
    # ---- BORED ----
    if robot.emotion == "IDLE" and now - robot.last_activity > 30:
        robot.emotion = "BORED"
        def reset_emotion():
            time.sleep(3)
            if robot.emotion == "BORED":
                robot.emotion = "IDLE"
        threading.Thread(target=reset_emotion, daemon=True).start()
    
    # ---- SLEEP (60 seconds of inactivity) ----
    if robot.emotion == "IDLE" and not robot.is_listening and not robot.is_speaking:
        if now - robot.sleep_timer > 60:  # Change 60 to your desired seconds
            robot.sleepy_mode = True
            robot.is_asleep = True
            robot.sleep_start_time = now
            print("Robot is sleeping... (click or press any key to wake up)")
            robot.emotion = "IDLE"
    # REMOVED the else block entirely to avoid confusion

def check_reminders():
    global reminders
    now = time.time()
    due_reminders = []
    for reminder in reminders[:]:
        if now >= reminder["time"]:
            due_reminders.append(reminder["message"])
            reminders.remove(reminder)
    for msg in due_reminders:
        print(f"⏰ Reminder: {msg}")
        speak_text(f"Reminder: {msg}")

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click = DRAG
                wake_up()
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 0x2, 0)
                print("Dragging window...")

            elif event.button == 3:  # Right click
                wake_up()
                robot.clicked = True
                robot.click_timer = time.time()
                robot.click_emotion = robot.emotion
                print("Robot clicked!")
                speak_text("Hee heee!")

        if event.type == pygame.KEYDOWN:
            wake_up()
            
            if event.key == pygame.K_ESCAPE:
                running = False
            
            if event.key == pygame.K_SPACE and not robot.is_listening:
                robot.is_listening = True
                robot.emotion = "LISTENING"
                robot.last_activity = time.time()
                print("🎤 Holding Space...")
            
            if event.key == pygame.K_h:
                robot.emotion = "HAPPY"
                robot.last_activity = time.time()
                def reset_emotion():
                    time.sleep(1.5)
                    if robot.emotion == "HAPPY":
                        robot.emotion = "IDLE"
                threading.Thread(target=reset_emotion, daemon=True).start()
            
            if event.key == pygame.K_s:
                robot.emotion = "SURPRISED"
                robot.last_activity = time.time()
                def reset_emotion():
                    time.sleep(1.5)
                    if robot.emotion == "SURPRISED":
                        robot.emotion = "IDLE"
                threading.Thread(target=reset_emotion, daemon=True).start()
            
            if event.key == pygame.K_c:
                robot.clicked = True
                robot.click_timer = time.time()
                robot.click_emotion = robot.emotion
                print(" Click test triggered!")
            
            if event.key == pygame.K_r:
                if user_facts:
                    facts = ", ".join([f"{k}: {v}" for k, v in user_facts.items()])
                    speak_text(f"I remember! {facts}")
                else:
                    speak_text("I don't know anything about you yet. Tell me your name or something about yourself!")
        
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and robot.is_listening:
                wake_up()
                robot.is_listening = False
                robot.last_activity = time.time()
                print("🛑 Processing...")
                threading.Thread(target=listen_and_process, daemon=True).start()
    
    # ---- Click timeout ----
    if robot.clicked and time.time() - robot.click_timer > 2.0:
        robot.clicked = False
        if robot.click_emotion not in ["IDLE", "LISTENING", "THINKING", "SPEAKING"]:
            robot.emotion = robot.click_emotion
        else:
            robot.emotion = "IDLE"
        robot.click_emotion = "IDLE"
    
    # ---- Updates ----
    update_blink()
    update_cursor_tracking()
    
    if robot.emotion == "IDLE" and not robot.is_listening and not robot.is_speaking:
        update_idle_behaviors()
    else:
        robot.last_activity = time.time()
        if not robot.is_asleep:
            robot.sleepy_mode = False
            # --- FIX: Don't reset sleep timer for internal emotions ---
            # Only reset if the user actually did something (LISTENING, THINKING, SPEAKING, HAPPY, SURPRISED)
            if robot.emotion not in ["BORED", "YAWN"]:
                robot.sleep_timer = time.time()
    
    # ---- Reminders ----
    if int(time.time()) % 1 == 0:
        check_reminders()
    
    # ---- Draw ----
    draw_face(screen, robot)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

#created on 24/06/2026