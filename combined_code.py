import asyncio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async
import pyaudio
import wave
import threading
import time
import speech_recognition as sr
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5  # Adjust as needed

audio = pyaudio.PyAudio()
r = sr.Recognizer()  # Create a recognizer instance

thread_running = False
recording = False
input_count = 0
waiting_for_text = False
chat_history = []  # The chat message history. The item is (name, message content)
online_users = set()

def get_genai_response(text_body):
    """Calls the Gemini model with text_body and returns the response."""
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    text_answer_model = genai.GenerativeModel('gemini-pro')
    response = text_answer_model.generate_content(str(text_body), stream=True)
    response.resolve()
    return response.text

def record_audio():
    global thread_running, recording, waiting_for_text
    while thread_running:  # Continuously check for recording flag
        if recording:
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK)

            frames = []

            while recording:
                data = stream.read(CHUNK)
                frames.append(data)

            stream.stop_stream()
            stream.close()

            filename = f"rec_data_{time.strftime('%Y%m%d_%H%M%S')}.wav"
            waveFile = wave.open(filename, 'wb')
            waveFile.setnchannels(CHANNELS)
            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
            waveFile.setframerate(RATE)
            waveFile.writeframes(b''.join(frames))

            try:
                with sr.AudioFile(filename) as source:
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)  # Transcribe using Google
                    # Print question and response
                    print("Question:", text)
                    genai_response = get_genai_response(text)
                    print("Response:", genai_response)
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

            waveFile.close()

            # Signal text display completion
            waiting_for_text = False
            return text, genai_response

async def refresh_msg():
    """send new message to current session"""
    global chat_history
    last_idx = len(chat_history)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_history[last_idx:]:
            put_markdown('`%s`: %s' % m, sanitize=True, scope='msg-box')

async def main():
    global chat_msgs

    put_markdown(("## PyWebIO Voxonomy Assistant\nWelcome to the Question Answering Voxonomy service. To use this app press any key + enter to begin recording your question. Then press any key + enter to finish. The Question will display, then an AI Answer will be supplied."))

    put_scrollable(put_scope('msg-box'), height=300, keep_bottom=True)
    nickname = "Intelligent Presenter"
    online_users.add(nickname)

    refresh_task = run_async(refresh_msg())

    while True:
        cue_data = await input_group(('Recording Cue'), [
            input(name='msg', help_text=('Press any key, then enter to begin recording')),
            actions(name='cmd', buttons=[('Send'), {'label': ('Exit'), 'type': 'cancel'}])
        ], validate=lambda d: ('msg', 'empty point') if d['cmd'] == ('Send') and not d['msg'] else None)
        if cue_data is None:
            break

        put_markdown('`%s`: %s' % (nickname, data['msg']), sanitize=True, scope='msg-box')
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()
    toast("You have left the chat room")

if __name__ == '__main__':
    start_server(main, debug=True, port=8080)

audio.terminate()  # Terminate PyAudio after the loop
print("Done!")