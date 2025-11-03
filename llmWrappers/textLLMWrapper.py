import os
import time
import threading

from llama_cpp import Llama
from constants import *
from llmWrappers.abstractLLMWrapper import AbstractLLMWrapper

class TextLLMWrapper(AbstractLLMWrapper):

    def __init__(self, signals, tts, llmState, modules=None):
        super().__init__(signals, tts, llmState, modules)
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.CONTEXT_SIZE = CONTEXT_SIZE

        model_path = os.getenv(
            "GGUF_MODEL_PATH",
            os.path.join("local_models", "gguf", MODEL)
        )

        self.llm = Llama(
            model_path=model_path,
            n_ctx=self.CONTEXT_SIZE,
            verbose=True,
        )

        self.max_tokens = 200
        self.temperature = 0.7
        self.top_p = 0.9
        self.repetition_penalty = 1.1

    def prompt(self):
        if not self.llmState.enabled:
            return

        self.signals.AI_thinking = True
        self.signals.new_message = False
        self.signals.sio_queue.put(("reset_next_message", None))

        prompt_text = self.generate_prompt()
        self.signals.history.append({"role": "user", "content": prompt_text})

        stream = self.llm(
            prompt=prompt_text,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repetition_penalty,
            stream=True
        )

        def async_play(text):
            threading.Thread(target=self.tts.play, args=(text,), daemon=True).start()

        response = ""
        buffer = ""

        for chunk in stream:
            token = chunk.get("choices", [{}])[0].get("text", "")
            if not token:
                continue

            response += token
            buffer += token
            self.signals.sio_queue.put(("next_chunk", token))

            if len(buffer) > 20 or token in ".!?":
                async_play(buffer.strip())
                buffer = ""

        if buffer.strip():
            async_play(buffer.strip())

        # response = ""
        # sentence_buffer = ""

        # for chunk in stream:
        #     try:
        #         token = chunk["choices"][0]["text"]
        #     except (KeyError, IndexError):
        #         continue

        #     response += token
        #     sentence_buffer += token
        #     self.signals.sio_queue.put(("next_chunk", token))

        #     # Nếu kết thúc câu thì phát luôn
        #     if sentence_buffer.strip().endswith((".", "!", "?")):
        #         self.tts.play(sentence_buffer.strip())
        #         sentence_buffer = ""

        # # Phát phần còn lại nếu chưa được đọc
        # if sentence_buffer.strip():
        #     self.tts.play(sentence_buffer.strip())

        response = response.strip()
        print("== FULL RESPONSE ==", response)

        self.signals.history.append({"role": "assistant", "content": response})
        self.signals.last_message_time = time.time()
        self.signals.AI_speaking = False
        self.signals.AI_thinking = False

        return response
