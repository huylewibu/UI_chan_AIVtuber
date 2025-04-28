import time
from constants import PATIENCE


class Prompter:
    def __init__(self, signals, llms, modules=None):
        self.signals = signals
        self.llms = llms
        if modules is None:
            self.modules = {}
        else:
            self.modules = modules

        self.system_ready = False
        self.timeSinceLastMessage = 0.0

    def prompt_now(self):
        # Không cho AI phản hồi nếu hệ thống chưa sẵn sàng
        if not self.signals.stt_ready or not self.signals.tts_ready:
            return False
        # Không cho AI phản hồi nếu ai đó đang nói hoặc AI đang suy nghĩ
        if self.signals.human_speaking or self.signals.AI_thinking or self.signals.AI_speaking:
            return False
        # Nếu người dùng vừa nói một câu mới
        if self.signals.new_message:
            return True
        # Nếu có tin nhắn chưa xử lý từ Twitch chat
        if len(self.signals.recentTwitchMessages) > 0:
            return True
        # Nếu đã vượt quá thời gian chờ mà không có ai nói
        if self.timeSinceLastMessage > PATIENCE:
            return True

    def chooseLLM(self):
        if "multimodal" in self.modules and self.modules["multimodal"].API.multimodal_now():
            return self.llms["image"]
        else:
            return self.llms["text"]

    def prompt_loop(self):
        print("Prompter loop started")

        while not self.signals.terminate:
            # Set lastMessageTime to now if program is still starting
            if self.signals.last_message_time == 0.0 or (not self.signals.stt_ready or not self.signals.tts_ready):
                self.signals.last_message_time = time.time()
                self.timeSinceLastMessage = 0.0
            else:
                if not self.system_ready:
                    print("SYSTEM READY")
                    self.system_ready = True

            # Calculate and set time since last message
            self.timeSinceLastMessage = time.time() - self.signals.last_message_time
            self.signals.sio_queue.put(("patience_update", {"crr_time": self.timeSinceLastMessage, "total_time": PATIENCE}))

            # Decide and prompt LLM
            if self.prompt_now():
                print("PROMPTING AI")
                llmWrapper = self.chooseLLM()
                llmWrapper.prompt()
                self.signals.last_message_time = time.time()

            # Sleep for 0.1 seconds before checking again.
            time.sleep(0.1)