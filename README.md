🤖 Denise - AI Desktop Companion Robot

https://img.shields.io/badge/Python-3.13-blue
https://img.shields.io/badge/Pygame-2.6.1-green
https://img.shields.io/badge/AI-Google%20Gemini-orange
https://img.shields.io/badge/License-MIT-yellow

    A cute, expressive, AI-powered desktop companion robot that lives on your Windows desktop. Talk to it, and it talks back with natural voice, remembers facts about you, reads you the weather, monitors your system, and reacts with lifelike emotions.

Created by Yasindu Sasmitha | Version 1.0
✨ Features
🎭 Lifelike Expressions

    Blinking with randomized timing (every 3-8 seconds)

    Eye tracking that follows your cursor

    Random look-around when you're idle (like Vector/Emo robots)

    Sleep mode after 60 seconds of inactivity

    Yawning when bored

    Emotional reactions – Happy, Surprised, Bored, Sleepy, Thinking, Clicking

🗣️ Natural Voice Interaction

    Push-to-talk with the Spacebar

    Speech-to-text using Google's free recognition API

    Natural voice output via Microsoft Edge-TTS (no robotic monotone!)

    Mouth animation synced to speech

🧠 AI Brain (Google Gemini)

    Powered by Gemini 2.0/3.1 Flash models

    Contextual conversations – remembers the last 10 exchanges

    Long-term memory – saves facts about you in user_facts.json

    Custom personality – playful, curious, empathetic companion

🌤️ Live Weather

    Real-time weather via OpenWeatherMap API

    Ask "What's the weather?" or press W

    Supports any city – "Weather in Tokyo"

🖥️ System Monitoring

    Real-time CPU, RAM, and disk usage via psutil

    Warns you when CPU is above 80%

    Press M to check system status

⏰ Reminders

    Voice command: "Remind me to [task] in [X] minutes"

    Robot speaks the reminder out loud when the time comes

🖱️ Desktop Integration

    Draggable window – left-click and drag anywhere

    Transparent background – floats over your wallpaper

    Borderless, always-on-top window

    Right-click reaction – the robot giggles when you click it

🎥 Demo


🚀 Getting Started
Prerequisites

    Windows 10/11 (uses Windows-specific APIs for dragging)

    Python 3.10+ (tested on 3.13.2)

    A microphone (for voice input)

    Internet connection (for Gemini, Edge-TTS, and weather)

1. Clone or Download the Project
bash

# Create the project folder
mkdir my_desktop_robot
cd my_desktop_robot

2. Create a Virtual Environment
bash

python -m venv venv
venv\Scripts\activate

3. Install Dependencies

Create a requirements.txt file with:
txt

pygame
SpeechRecognition
edge-tts
requests
google-genai
python-dotenv
psutil
pyaudio

Then install:
bash

pip install -r requirements.txt

    ⚠️ If PyAudio fails to install, run:
    bash

    pip install pipwin
    pipwin install pyaudio

4. Get API Keys
🔑 Google Gemini API Key (Required for AI)

    Go to Google AI Studio

    Click "Get API Key" → "Create API Key"

    Copy the key and keep it safe.

🔑 OpenWeatherMap API Key (For weather)

    Sign up at OpenWeatherMap

    Copy your free API key.

5. Configure Environment Variables

Create a .env file in the project root:
env

GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

Then update the code to use them (see main.py for reference):
python

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

6. Prepare Your Assets

Create an assets/ folder inside your project and add these PNG files (transparent background, matching dimensions):
text

assets/
├── face_base.png          # Dark rounded face background
├── eyes_idle.png          # Default blue eyes
├── eyes_listening.png     # Yellow listening eyes
├── eyes_closed.png        # Closed eyes (for blinking)
├── eyes_think.png         # Thinking eyes
├── eyes_happy.png         # Happy sparkle eyes
├── eyes_surprised.png     # Surprised wide eyes
├── eyes_sleep.png         # Sleepy half-closed eyes
├── eyes_click.png         # Reaction eyes for clicking
├── mouth_talk_1.png       # Talking mouth frame 1
├── mouth_talk_2.png       # Talking mouth frame 2
├── mouth_yawn.png         # Yawning mouth
└── mouth_frown.png        # Bored frown (optional)

7. Run the Robot
bash

python main.py

Your robot should appear on screen! 🎉
🎮 Controls
Keyboard
Key	Action
SPACE (hold)	Record your voice – release to process
W	Get weather for the default city
M	Get system status (CPU, RAM, disk)
R	Ask what the robot remembers about you
H	Trigger happy expression
S	Trigger surprised expression
C	Trigger click reaction
ESC	Close the robot
Mouse
Button	Action
Left-click + drag	Move the robot window
Right-click	Click reaction (robot says "Hee heee!")
Voice Commands

Hold SPACE and say:
Command	What it does
"What's the weather?"	Reports current weather
"Weather in London"	Weather for a specific city
"How is my system doing?"	Reports CPU, RAM, disk
"Remind me to call John in 5 minutes"	Sets a reminder
"What do you remember about me?"	Lists saved facts
Anything else	Chats via Gemini AI
🗂️ Project Structure
text

my_desktop_robot/
│
├── main.py                 # The main application
├── requirements.txt        # Python dependencies
├── .env                    # API keys (DO NOT commit!)
├── user_facts.json         # Auto-generated memory file
├── README.md               # This file
│
└── assets/                 # Custom PNG images
    ├── face_base.png
    ├── eyes_idle.png
    ├── eyes_listening.png
    ├── eyes_closed.png
    ├── eyes_think.png
    ├── eyes_happy.png
    ├── eyes_surprised.png
    ├── eyes_sleep.png
    ├── eyes_click.png
    ├── mouth_talk_1.png
    ├── mouth_talk_2.png
    ├── mouth_yawn.png
    └── mouth_frown.png

🧠 How It Works
Architecture Overview
text

┌─────────────────────────────────────────────────────┐
│                    Pygame Window                    │
│  ┌───────────────┐                                  │
│  │  Base Face    │  ← face_base.png                 │
│  ├───────────────┤                                  │
│  │  Eyes Layer   │  ← Dynamic based on state        │
│  ├───────────────┤                                  │
│  │  Mouth Layer  │  ← Only when needed              │
│  └───────────────┘                                  │
└─────────────────────────────────────────────────────┘
            ▲                    │
            │                    ▼
    ┌───────┴────────┐   ┌──────────────┐
    │ Emotion State  │   │ RobotState   │
    │  Machine       │◄──┤ (Python)     │
    └───────┬────────┘   └──────────────┘
            │
    ┌───────┴────────┬─────────────┬─────────────┐
    │                │             │             │
    ▼                ▼             ▼             ▼
┌────────┐    ┌────────────┐  ┌────────┐  ┌──────────┐
│ Gemini │    │Edge-TTS    │  │Weather │  │ psutil   │
│  AI    │    │(Voice Out) │  │  API   │  │(System)  │
└────────┘    └────────────┘  └────────┘  └──────────┘

Emotion State Machine

The robot cycles through these states based on context:

    IDLE → Default state (blue eyes)

    LISTENING → Holding Spacebar (yellow eyes)

    THINKING → Waiting for AI response (looking-up eyes)

    SPEAKING → Playing TTS audio (animated mouth)

    HAPPY → After good interaction (sparkle eyes)

    SURPRISED → Unexpected events (wide eyes)

    BORED → 30s+ no interaction (frown mouth)

    YAWNING → 45-90s idle (open mouth)

    SLEEPING → 60s+ idle (closed eyes)

    CLICKED → On right-click (special eyes)

⚙️ Customization
1. Change the Robot's Name

In get_gemini_response(), update the system prompt:
python

system_prompt = """You are YOUR_NAME, a playful desktop robot..."""

2. Change the Voice

In speak_text(), change the voice code:
python

communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", pitch="+25Hz")

Popular voices:
Voice Code	Description
en-US-JennyNeural	Natural female (US)
en-US-GuyNeural	Natural male (US)
en-GB-SoniaNeural	Friendly female (British)
en-GB-RyanNeural	Calm male (British)
en-AU-NatashaNeural	Cheerful female (Australian)
en-IN-NeerjaNeural	Warm female (Indian)

Run edge-tts --list-voices in the terminal to see all options.
3. Adjust Sleep Time

In update_idle_behaviors():
python

if now - robot.sleep_timer > 60:  # Change 60 to your desired seconds

4. Change the Default City
python

DEFAULT_CITY = "Colombo"  # Change to your city

5. Tune the Personality

Edit the system_prompt in get_gemini_response() to change:

    Tone (playful, serious, sarcastic)

    Response length

    Topics the robot loves

    Behavioral rules

6. Adjust Eye/Mouth Movement

In update_cursor_tracking():
python

robot.eye_target_x = max(-35, min(35, dx * 0.2))  # Adjust range and sensitivity
robot.eye_current_x += (robot.eye_target_x - robot.eye_current_x) * 0.06  # Adjust speed

🐛 Troubleshooting
Robot says "Could not understand audio"

    Speak louder and closer to the mic

    Check Windows microphone permissions: Settings → Privacy → Microphone

    The recognize_google function requires internet

PyAudio installation fails
bash

pip install pipwin
pipwin install pyaudio

Gemini returns errors

    Verify your .env has the correct GEMINI_API_KEY

    Check your internet connection

    Check that your API key hasn't been revoked in AI Studio

Weather says "Couldn't get weather"

    Check your OPENWEATHER_API_KEY is valid

    Try a different city name

    Free OpenWeatherMap keys take ~10 minutes to activate after signup

Robot is not sleeping

    Make sure nothing keeps resetting sleep_timer (see BORED/YAWN exclusion in main loop)

    Lower the sleep threshold for testing (set to 10 seconds)

Window keeps appearing on top

    This is intentional (always-on-top). To disable, look for pygame.NOFRAME in the window setup and remove | pygame.SRCALPHA (not recommended).

🛣️ Roadmap

Ideas for future versions:

    □

    Wake word detection ("Hey Denys" instead of Spacebar)
    □

    Click-through mode (interact with apps behind the robot)
    □

    Document reader (PDF, DOCX, TXT → AI summaries)
    □

    Web search (real-time info via SerpAPI)
    □

    Vision mode (webcam input for Gemini multimodal)
    □

    Voice emotion detection (adjust responses to your mood)
    □

    Multi-language support
    □

    Custom sprite themes (change robot appearance)
    □

    Scheduled reminders ("Remind me at 3 PM to call John")
    □

    Daily greetings based on time of day

🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to:

    Fork this project

    Create a feature branch

    Submit a pull request

📜 License

This project is licensed under the MIT License – see below for details.
text

MIT License

Copyright (c) 2026 Yasindu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

🙏 Credits & Acknowledgments

    Inspiration: Anki Vector, Emo (Living AI), and Cozmo

    AI: Google Gemini

    Voice: Microsoft Edge TTS

    Graphics Engine: Pygame

    Speech Recognition: SpeechRecognition

    Weather: OpenWeatherMap

    System Monitoring: psutil

📞 Contact

Yasindu — Project Creator

    GitHub: @Yasindu-Sasmitha

    Email: yasindusasmitha@gmail.com

<p align="center"> <strong>⭐ If you enjoyed this project, give it a star! ⭐</strong><br> <em>Built with ❤️, Python, and a lot of curiosity.</em> </p>
