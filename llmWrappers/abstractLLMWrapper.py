import copy
import requests
from dotenv import load_dotenv
from constants import *
from modules.injection import Injection

class AbstractLLMWrapper:

    def __init__(self, signals, tts, llmState, modules=None):
        self.signals = signals
        self.llmState = llmState
        self.tts = tts
        self.API = self.API(self)
        if modules is None:
            self.modules = {}
        else:
            self.modules = modules

        self.headers = {"Content-Type": "application/json"}

        load_dotenv()

        # Class con phải ghi đè mấy thằng này
        self.SYSTEM_PROMPT = None
        self.LLM_ENDPOINT = None
        self.CONTEXT_SIZE = None
        self.tokenizer = None

    # Filter đơn giản để kiểm tra từ cấm
    def is_filtered(self, text):
        # Filter messages với mấy từ trong blacklist
        if any(bad_word.lower() in text.lower().split() for bad_word in self.llmState.blacklist):
            return True
        return False

    # Ghép lại injection từ tất cả module vào một prompt đơn giản
    def assemble_injections(self, injections=None):
        if injections is None:
            injections = []

        # Tập hợp tất cả injection từ mọi module vào một cái list, injection sẽ là một object gồm text và priority
        for module in self.modules.values():
            injections.append(module.get_prompt_injection())
        # Xoá các modules khỏi queue một khi prompt injection được lấy từ tất cả các modules
            module.cleanup()

        # Sắp xếp injections theo priority ( nhỏ hơn đến lớn hơn )
        injections = sorted(injections, key=lambda x: x.priority)

        # Tập hợp injections thành một cái string
        prompt = ""
        for injection in injections:
            prompt += injection.text
        return prompt

    def generate_prompt(self):
        messages = copy.deepcopy(self.signals.history)

        # Thêm prefix cho từng câu để nhận biết ai là người đang gửi tin nhắn (trừ khi câu đéo có gì)
        for message in messages:
            if message["role"] == "user" and message["content"] != "":
                message["content"] = HOST_NAME + ": " + message["content"] + "\n"
            elif message["role"] == "assistant" and message["content"] != "":
                message["content"] = AI_NAME + ": " + message["content"] + "\n"

        while True:
            chat_section = ""
            for message in messages:
                chat_section += message["content"]

            # Bảo AI tự điền phần còn thiếu sau đoạn hội thoại
            generation_prompt = AI_NAME + ": "

            base_injections = [Injection(self.SYSTEM_PROMPT, 10), Injection(chat_section, 100)]
            full_prompt = self.assemble_injections(base_injections) + generation_prompt
            wrapper = [{"role": "user", "content": full_prompt}]

            # Xem thử có bao nhiêu token trong prompt (Không chính xác 100% nhưng vẫn ổn để ước lượng)
            prompt_text = self.SYSTEM_PROMPT + "\n"
            for message in self.signals.history:
                role = message["role"]
                content = message["content"]
                prompt_text += f"{role.capitalize()}: {content}\n"
            prompt_text += "Assistant:"

            prompt_tokens = len(prompt_text.split())
            # print(prompt_tokens)

            # Max 90% số token trong prompt để LLM có thể trả lời
            if prompt_tokens < 0.9 * self.CONTEXT_SIZE:
                self.signals.sio_queue.put(("full_prompt", full_prompt))
                # print(full_prompt)
                return full_prompt
            else:
                # Check lỗi nếu prompt bị báo quá dài nhưng thực tế không có message nào
                if len(messages) < 1:
                    raise RuntimeError("Prompt too long even with no messages")

                # Xoá message cũ nhất trong prompt và thử lại
                messages.pop(0)
                print("Prompt too long, removing earliest message")

    def prompt(self):
        raise NotImplementedError("Child class must implement its own prompt() method.")

    class API:
        def __init__(self, outer):
            self.outer = outer

        def get_blacklist(self):
            return self.outer.llmState.blacklist

        def set_blacklist(self, new_blacklist):
            self.outer.llmState.blacklist = new_blacklist
            with open('blacklist.txt', 'w') as file:
                for word in new_blacklist:
                    file.write(word + "\n")

            # Notify clients
            self.outer.signals.sio_queue.put(('get_blacklist', new_blacklist))

        def set_LLM_status(self, status):
            self.outer.llmState.enabled = status
            if status:
                self.outer.signals.AI_thinking = False
            self.outer.signals.sio_queue.put(('LLM_status', status))

        def get_LLM_status(self):
            return self.outer.llmState.enabled

        def cancel_next(self):
            self.outer.llmState.next_cancelled = True
            # For text-generation-webui: Immediately stop generation
            requests.post(self.outer.LLM_ENDPOINT + "/v1/internal/stop-generation", headers={"Content-Type": "application/json"})