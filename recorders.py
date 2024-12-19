import pyaudio
import wave
from faster_whisper import WhisperModel

class AudioRecorder:
    def __init__(
        self, 
        filename="audio.wav", 
        chunk=1024, 
        sample_format=pyaudio.paInt16, 
        channels=2, 
        fs=44100, 
        seconds=6
    ):
        self.filename = filename
        self.chunk = chunk
        self.sample_format = sample_format
        self.channels = channels
        self.fs = fs
        self.seconds = seconds
        self.model = self.load_model_stt()

    def load_model_stt(self):
        model = WhisperModel("base", device="cpu", compute_type="int8")
        return model

    def listen(self):
        print('Recording')

        p = pyaudio.PyAudio()

        stream = p.open(
            format=self.sample_format,
            channels=self.channels,
            rate=self.fs,
            frames_per_buffer=self.chunk,
            input=True
        )

        frames = []

        for i in range(0, int(self.fs / self.chunk * self.seconds)):
            data = stream.read(self.chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        print('Finished recording')

        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b''.join(frames))
        wf.close()

        segments, info = self.model.transcribe(self.filename, beam_size=1, language="it")

        requests = " ".join([segment.text for segment in segments])

        return requests
    
    
