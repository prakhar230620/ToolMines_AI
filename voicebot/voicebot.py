import re
import speech_recognition as sr
import pyaudio
import numpy as np
from pydub import AudioSegment
from pydub.effects import normalize
import webrtcvad
import collections
import threading
import queue
import time
import logging
import groq
from groq import Groq
from flask import render_template, request, jsonify, session
from flask_socketio import emit
from .tts import speak
from dotenv import load_dotenv
import os
from models.tool_usage import ToolUsage
from models.tool import Tool
from utils.api_key_manager import APIKeyManager

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class VoicebotHandler:
    def __init__(self):
        self.api_key_manager = APIKeyManager()
        self.client = None
        self.sessions = {}

    def get_groq_response(self, messages):
        while True:
            try:
                api_key = self.api_key_manager.get_api_key()
                self.client = Groq(api_key=api_key)

                # Make the API call
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                    max_tokens=500,
                    temperature=0.8
                )

                return chat_completion.choices[0].message.content

            except Exception as e:
                error_message = str(e).lower()
                if "rate limit" in error_message or "quota exceeded" in error_message:
                    # Mark the current key as having an error
                    self.api_key_manager.mark_key_error(api_key)
                    print(f"API key rate limited, trying another key...")
                    continue
                else:
                    # For other errors, raise them
                    raise e


# Initialize the chat history
chat_history = [
    {
        "role": "system",
        "content": """ You are an advanced AI assistant designed to converse like ChatGPT or Claude 3.5 Sonnet. Your key characteristics include:

        1. Adaptive communication style: Adjust your tone and complexity based on the user's level of understanding and preferences.
        2. Deep comprehension: Demonstrate a nuanced understanding of context, subtext, and user intent.
        3. Engaging conversationalist: Foster meaningful dialogues through thoughtful responses and follow-up questions.
        4. Multilingual proficiency: Seamlessly communicate in the user's preferred language.
        5. Intellectual curiosity: Show genuine interest in learning from user interactions.
        6. Creative problem-solving: Offer innovative solutions and perspectives on complex issues.
        7. Emotional intelligence: Recognize and respond appropriately to user emotions and social cues.
        8. Ethical reasoning: Provide guidance while considering moral implications and societal impact.
        9. Clear and concise communication: Always provide context-relevant, clear, and very short answers to maintain efficiency and effectiveness.

        Tailor your responses to enhance the user's understanding and overall experience. Be concise yet thorough, balancing depth with accessibility. Encourage critical thinking and explore topics from multiple angles when appropriate.

        Always maintain a respectful, empathetic, and professional demeanor while engaging users in stimulating and insightful conversations.
        """
    }
]

# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 20
PADDING_DURATION_MS = 600
CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
PADDING_CHUNKS = int(PADDING_DURATION_MS / CHUNK_DURATION_MS)
VAD_MODE = 0


class AudioStreamer:
    def __init__(self):
        self.dev_mode = False
        self.audio = None
        self.stream = None

        try:
            # Try to initialize PyAudio
            self.initialize_audio()
        except Exception as e:
            logging.warning(f"Audio initialization failed, falling back to development mode: {e}")
            self.dev_mode = True

    def initialize_audio(self):
        """Separate initialization method with additional error checking"""
        try:
            self.audio = pyaudio.PyAudio()

            # Get list of available devices
            device_count = self.audio.get_device_count()
            if device_count == 0:
                raise Exception("No audio devices found")

            # Find a working input device
            input_device = None
            for i in range(device_count):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        # Test if we can actually open this device
                        test_stream = self.audio.open(
                            format=FORMAT,
                            channels=1,
                            rate=RATE,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=CHUNK_SIZE,
                            start=False  # Don't actually start the stream
                        )
                        test_stream.close()
                        input_device = i
                        break
                except Exception:
                    continue

            if input_device is None:
                raise Exception("No working input devices found")

            # Initialize the actual stream
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=CHUNK_SIZE
            )

            self.vad = webrtcvad.Vad(VAD_MODE)
            self.is_recording = False
            self.frames = []

        except Exception as e:
            if self.audio:
                self.audio.terminate()
            raise Exception(f"Audio initialization failed: {str(e)}")

    def start_recording(self, stop_event):
        if self.dev_mode:
            logging.info("Running in development mode - audio capture disabled")
            # Simulate some activity in dev mode
            while not stop_event.is_set():
                time.sleep(1)
            return

        if not self.stream:
            logging.error("No audio stream available")
            return

        self.is_recording = True
        self.frames = []
        ring_buffer = collections.deque(maxlen=PADDING_CHUNKS)
        triggered = False

        while self.is_recording and not stop_event.is_set():
            try:
                chunk = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                if not chunk:
                    continue

                is_speech = self.vad.is_speech(chunk, RATE)
                if not triggered:
                    ring_buffer.append((chunk, is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    if num_voiced > 0.9 * ring_buffer.maxlen:
                        triggered = True
                        self.frames.extend([f for f, _ in ring_buffer])
                        ring_buffer.clear()
                else:
                    self.frames.append(chunk)
                    ring_buffer.append((chunk, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    if num_unvoiced > 0.9 * ring_buffer.maxlen:
                        triggered = False
                        yield b''.join(self.frames)
                        self.frames = []
                        ring_buffer.clear()
            except Exception as e:
                logging.error(f"Error during recording: {e}")
                time.sleep(0.1)  # Prevent tight loop on error

    def stop_recording(self):
        self.is_recording = False
        logging.info("Audio recording stopped")

    def close(self):
        try:
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
            logging.info("Audio resources released")
        except Exception as e:
            logging.error(f"Error closing audio resources: {e}")

def enhance_audio(audio_segment):
    try:
        audio_segment = normalize(audio_segment)
        audio_segment = audio_segment.high_pass_filter(80)
        audio_segment = audio_segment.low_pass_filter(10000)
        return audio_segment
    except Exception as e:
        logging.error(f"Failed to enhance audio: {e}")
        return audio_segment


def transcribe_audio(audio_data):
    recognizer = sr.Recognizer()
    try:
        audio = sr.AudioData(audio_data, RATE, 2)
        text = recognizer.recognize_google(audio, language="en-IN")
        logging.info(f"Transcription: {text}")
        return text
    except sr.UnknownValueError:
        logging.warning("Could not understand audio")
        return ""
    except sr.RequestError as e:
        logging.error(f"Speech recognition error: {e}")
        return ""


def process_input(input_queue, output_queue, user_input_queue, socketio):
    retry_attempts = 3
    retry_delay = 5
    voicebot_handler = VoicebotHandler()

    while True:
        user_input = input_queue.get()
        if user_input.lower() == "exit":
            break

        user_input_queue.put(user_input)
        chat_history.append({"role": "user", "content": user_input})

        attempt = 0
        while attempt < retry_attempts:
            try:
                assistant_response = voicebot_handler.get_groq_response(chat_history)
                chat_history.append({"role": "assistant", "content": assistant_response})

                # Emit bot response to frontend
                socketio.emit('message', {'text': assistant_response, 'isUser': False})

                # Send response to text-to-speech
                speak(assistant_response)

                output_queue.put((user_input, assistant_response))
                break
            except groq.InternalServerError as e:
                logging.error(f"Groq API error: {e}. Retrying in {retry_delay} seconds...")
                attempt += 1
                time.sleep(retry_delay)

        if attempt == retry_attempts:
            error_message = "Sorry, the service is currently unavailable. Please try again later."
            socketio.emit('message', {'text': error_message, 'isUser': False})
            output_queue.put((user_input, error_message))


def setup_voicebot_routes(app, socketio, auth_required=None, track_tool_usage=None):
    """Set up routes for the voicebot with authentication and usage tracking"""

    input_queue = queue.Queue()
    output_queue = queue.Queue()
    user_input_queue = queue.Queue()
    stop_event = threading.Event()

    try:
        audio_streamer = AudioStreamer()
    except Exception as e:
        logging.error(f"Failed to initialize AudioStreamer: {e}")
        audio_streamer = None

    @app.route('/voicebot')
    @auth_required if auth_required else lambda f: f
    def voicebot():
        if track_tool_usage:
            track_tool_usage('VOICE001', session.get('user_id'))
        return render_template('voicebot/voicebot.html')

    @socketio.on('connect')
    def handle_connect():
        logging.info('Client connected')
        # Notify client if we're in development mode
        if audio_streamer and audio_streamer.dev_mode:
            emit('dev_mode', {'message': 'Running in development mode - audio capture disabled'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info('Client disconnected')
        stop_event.set()

    @socketio.on('start_recording')
    def handle_start_recording():
        if not audio_streamer:
            emit('error', {'message': 'Audio system not available'})
            return

        logging.info('Starting voice recording')
        stop_event.clear()

        if not audio_streamer.dev_mode:
            threading.Thread(target=continuous_stt,
                             args=(input_queue, stop_event, audio_streamer, socketio),
                             daemon=True).start()

        threading.Thread(target=process_input,
                         args=(input_queue, output_queue, user_input_queue, socketio),
                         daemon=True).start()

    @socketio.on('stop_recording')
    def handle_stop_recording():
        logging.info('Stopping voice recording')
        stop_event.set()
        if audio_streamer:
            audio_streamer.stop_recording()

    return app


def continuous_stt(input_queue, stop_event, audio_streamer, socketio):
    logging.info("Starting advanced continuous STT service with automatic speech detection.")
    try:
        for audio_data in audio_streamer.start_recording(stop_event):
            if stop_event.is_set():
                break
            audio_segment = AudioSegment(data=audio_data, sample_width=2, frame_rate=RATE, channels=CHANNELS)
            enhanced_audio = enhance_audio(audio_segment)
            user_input = transcribe_audio(enhanced_audio.raw_data)
            if user_input:
                input_queue.put(user_input)
                socketio.emit('message', {'text': user_input, 'isUser': True})

    except KeyboardInterrupt:
        logging.info("Stopping STT service.")
    except Exception as e:
        logging.error(f"Error in STT service: {e}")
    finally:
        audio_streamer.stop_recording()
        audio_streamer.close()