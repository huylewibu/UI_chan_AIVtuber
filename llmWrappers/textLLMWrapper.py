import os
import torch
import time

from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from constants import *
from llmWrappers.abstractLLMWrapper import AbstractLLMWrapper


class TextLLMWrapper(AbstractLLMWrapper):

    def __init__(self, signals, tts, llmState, modules=None):
        super().__init__(signals, tts, llmState, modules)
        self.SYSTEM_PROMPT = SYSTEM_PROMPT
        self.LLM_ENDPOINT = LLM_ENDPOINT
        self.CONTEXT_SIZE = CONTEXT_SIZE

        self.generation_config = GenerationConfig(
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.eos_token_id
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL, 
            token=os.getenv("HF_TOKEN"),
            cache_dir="./local_models/llama3-8b",
            trust_remote_code=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL,
            cache_dir="./local_models/llama3-8b",
            trust_remote_code=True,
            torch_dtype=torch.float16,
            token=os.getenv("HF_TOKEN"),
            device_map="auto",
            max_memory={0: "5GiB"}
        )
        self.model.eval()

    def prompt(self):
        if not self.llmState.enabled:
            return

        self.signals.AI_thinking = True
        self.signals.new_message = False
        self.signals.sio_queue.put(("reset_next_message", None))

        # Tạo prompt
        prompt_text = self.generate_prompt()

        # Tokenize, trả về tensor của pytorch rồi đẩy tensor vào thiết bị model đang ở (Cuda hoặc CPU)
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.model.device)

        # Generate output
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                generation_config=self.generation_config
            )

        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("GENERATED TEXT:", generated_text)
        # Tách phần trả lời của AI
        # input_len = inputs["input_ids"].shape[1]  # Số token đầu vào
        # generated_ids = outputs[0][input_len:]    # Lấy token phần sinh thêm
        # generated_response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        generated_response = generated_text[len(prompt_text):].strip()
        # generated_response = generated_text.removeprefix(prompt_text).strip()

        print("AI SAID:", generated_response)

        if self.is_filtered(generated_response):
            generated_response = "Filtered."

        self.signals.last_message_time = time.time()
        self.signals.AI_speaking = True
        self.signals.AI_thinking = False

        self.signals.history.append({"role": "assistant", "content": generated_response})
        self.signals.sio_queue.put(("next_chunk", generated_response))
        self.tts.play(generated_response)