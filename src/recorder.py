import pyaudio
import wave
from faster_whisper import WhisperModel
import numpy as np
import torch
from time import time

# questa funzione serve per convertire l'audio da int16 a float32
# in modo da poterlo passare al modello di VAD
# inoltre, normalizza l'audio
def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()
    return sound

class AudioRecorder:
    def __init__(self):
        self.stt_model = self.load_stt_model()
        self.vad_model = self.load_vad_model()

    def load_stt_model(self):
        model = WhisperModel("base", device="cpu", compute_type="int8")
        return model
    
    def load_vad_model(self):
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad'
        )
        return model
    
    def listen(self):

        filename = "data/audio.wav"
        sample_format = pyaudio.paInt16
        channels = 1
        frame_rate = 16000

        p = pyaudio.PyAudio()

        stream = p.open(
            format=sample_format,
            channels=channels,
            rate=frame_rate,
            frames_per_buffer=512,
            input=True
        )

        frames = []

        voice_detected_prob = 0
        trigger_listen = False
        no_talk_time = 0
        global_time = 0
        start_global_time = time()

        print("AUDIO - Start listening")
        while no_talk_time < 3 and global_time < 15:
            
            audio_chunk = stream.read(512)
            frames.append(audio_chunk)
            audio_int16 = np.frombuffer(audio_chunk, np.int16)
            audio_float32 = int2float(audio_int16)
            voice_detected_prob = self.vad_model(torch.from_numpy(audio_float32), 16000).item()

            if voice_detected_prob > 0.8:
                if not trigger_listen:
                    print("AUDIO - Voice detected!")
                trigger_listen = True
                no_talk_time = 0
                start_no_talk_time = time()

            elif trigger_listen:
                end_no_talk_time = time()
                no_talk_time = end_no_talk_time - start_no_talk_time

            end_global_time = time()
            global_time = end_global_time - start_global_time

        stream.stop_stream()
        stream.close()
        p.terminate()

        print('AUDIO - Finished listening')

        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(frame_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        segments, info = self.stt_model.transcribe(filename, beam_size=1, language="it")

        requests = " ".join([segment.text for segment in segments])

        return requests
