import pyaudio
import wave
import threading
import time
import speech_recognition as sr

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

def record_audio():
    global thread_running, recording

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

            filename = f"rec_data_{time.strftime('%Y%m%d_%H%M%S')}.wav"  # Assign filename
            waveFile = wave.open(filename, 'wb')  # Open with filename
            waveFile.setnchannels(CHANNELS)
            waveFile.setsampwidth(audio.get_sample_size(FORMAT))
            waveFile.setframerate(RATE)
            waveFile.writeframes(b''.join(frames))

            try:
                with sr.AudioFile(filename) as source:  # Use filename for AudioFile
                    audio_data = r.record(source)
                    text = r.recognize_google(audio_data)  # Transcribe using Google
                    print("Recognized text:", text)
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

            waveFile.close()

def take_input():
    global thread_running, recording, input_count

    user_input = input("Enter input: ")
    input_count += 1  # Increment input count

    if user_input:
        if input_count % 2 == 1:  # Odd input
            if not thread_running:
                thread_running = True
                t1.start()  # Start recording thread if not already running
            recording = True  # Begin recording
            if user_input.lower() == "exit":  # Check for "exit" on odd input
                thread_running = False  # Terminate if "exit"
        else:  # Even input
            recording = False  # Stop recording

if __name__ == "__main__":
    t1 = threading.Thread(target=record_audio)

    while True:
        take_input()
        if not thread_running:
            break

    audio.terminate()  # Terminate PyAudio after the loop
    print("Done!")