import os
from math import ceil
import asyncio
import queue
import pyaudio
from pydub import AudioSegment
from modules.module import Module
from constants import OUTPUT_DEVICE_INDEX


class AudioPlayer(Module):
    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.play_queue = queue.SimpleQueue()
        self.abort_flag = False
        self.paused = False
        self.API = self.API(self)

        if not self.enabled:
            return

        # Tìm nhạc trong folder songs (.mp3 và .wav)
        self.audio_files = []
        for dirpath, dirnames, filenames in os.walk("songs"):
            for file in filenames:
                if file.endswith(".mp3") or file.endswith(".wav"):
                    audio = self.Audio(file, os.path.join(os.getcwd(), "songs", file))
                    self.audio_files.append(audio)

    async def run(self):
        while not self.signals.terminate:

            # Module này không thể bật/tắt từ control panel, nếu tắt sẽ thoát luôn
            if not self.enabled:
                return

            # 	Nếu hiện tại không đang phát nhạc thì bỏ cờ dừng phát
            self.abort_flag = False

            if self.play_queue.qsize() > 0:
                file_name = self.play_queue.get()
                print(file_name)
                for audio in self.audio_files:
                    if audio.file_name == file_name:
                        print(f"Playing {audio.path}")
                        self.signals.AI_speaking = True

                        # Play the audio file
                        audio = AudioSegment.from_file(audio.path)
                        p = pyaudio.PyAudio()
                        stream = p.open(format=p.get_format_from_width(audio.sample_width),
                                        channels=audio.channels,
                                        rate=audio.frame_rate,
                                        output_device_index=OUTPUT_DEVICE_INDEX,
                                        output=True)

                        # Để tránh lỗi, luôn giải phóng tài nguyên âm thanh dù xảy ra lỗi bất ngờ
                        try:
                            # break audio into half-second chunks (to allows keyboard interrupts & aborts)
                            for chunk in make_chunks(audio, 200):
                                while self.paused:
                                    if self.abort_flag:
                                        break
                                    await asyncio.sleep(0.1)

                                if self.abort_flag:
                                    self.abort_flag = False
                                    break

                                stream.write(chunk._data)

                                # Gửi yield 0s để nhường quyền chạy cho các thread khác khi đang phát âm thanh
                                await asyncio.sleep(0)
                        finally:
                            stream.stop_stream()
                            stream.close()

                            p.terminate()
                            self.signals.AI_speaking = False

                        # Only play the first match
                        break

            await asyncio.sleep(0.1)

    class Audio:
        def __init__(self, file_name, path):
            self.file_name = file_name
            self.path = path

    class API:
        def __init__(self, outer):
            self.outer = outer

        def get_audio_list(self):
            filenames = []
            for audio in self.outer.audio_files:
                filenames.append(audio.file_name)
            return filenames

        def play_audio(self, file_name):
            self.stop_playing()
            self.outer.play_queue.put(file_name)

        def pause_audio(self):
            self.outer.paused = True

        def resume_audio(self):
            self.outer.paused = False

        def stop_playing(self):
            self.outer.abort_flag = True


# FROM PYDUB utils.py
def make_chunks(audio_segment, chunk_length):
    """
    Breaks an AudioSegment into chunks that are <chunk_length> milliseconds
    long.
    if chunk_length is 50 then you'll get a list of 50 millisecond long audio
    segments back (except the last one, which can be shorter)
    """
    number_of_chunks = ceil(len(audio_segment) / float(chunk_length))
    return [audio_segment[i * chunk_length:(i + 1) * chunk_length]
            for i in range(int(number_of_chunks))]