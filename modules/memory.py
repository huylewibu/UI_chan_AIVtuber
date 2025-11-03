from modules.module import Module
from constants import *
from chromadb.config import Settings
import chromadb # Vector database cho AI LLM
import torch
import json
import uuid
import asyncio
import copy


class Memory(Module):

    def __init__(self, signals, enabled=True):
        super().__init__(signals, enabled)

        self.API = self.API(self)
        self.prompt_injection.text = ""
        self.prompt_injection.priority = 60

        self.processed_count = 0

        # Lưu dữ liệu vào chroma.db
        self.chroma_client = chromadb.PersistentClient(path="./memories/chroma.db", settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma_client.get_or_create_collection(name="ui_collection")
        print(f"MEMORY: Loaded {self.collection.count()} memories from database.")
        # Nếu database không có memory nào thì tự động nhập file memoryinit.json
        if self.collection.count() == 0:
            print("MEMORY: No memories found in database. Importing from memoryinit.json")
            self.API.import_json(path="./memories/memoryinit.json")

    def get_prompt_injection(self):
        # Sử dụng tin nhắn gần đây và tin nhắn từ twitch để truy vấn database tìm kiếm các memory liên quan
        query = ""

        # chatMessage1\nchatMessage2\nchatMessage3\n...
        for message in self.signals.recentTwitchMessages:
            query += message + "\n"

        # Gán message cho đúng người để chromadb dễ nhận diện
        for message in self.signals.history[-MEMORY_QUERY_MESSAGE_COUNT:]:
            if message["role"] == "user" and message["content"] != "":
                query += HOST_NAME + ": " + message["content"] + "\n"
            elif message["role"] == "assistant" and message["content"] != "":
                query += AI_NAME + ": " + message["content"] + "\n"

        # memories sẽ là một object có các thuộc tính ids(list id memory tìm được), documents(list 
        # nội dung kí ức dạng text), distances(độ gần gũi với query)
        memories = self.collection.query(query_texts=query, n_results=MEMORY_RECALL_COUNT)

        # Thêm context history tìm được để chèn vào prompt giúp AI nhớ được kí ức
        self.prompt_injection.text = f"{AI_NAME} knows these things:\n"
        # for i in range(len(memories["ids"][0])):
        #     self.prompt_injection.text += memories['documents'][0][i] + "\n"
        for doc in memories["documents"][0]:
            self.prompt_injection.text += doc + "\n"
        self.prompt_injection.text += "End of knowledge section\n"

        return self.prompt_injection

    async def run(self):
        while not self.signals.terminate:
            # Tránh lỗi tràn index nếu số lượng tin nhắn đã xử lí nhiều hơn độ dài hiện tại của history (history bị xoá bớt)
            if self.processed_count > len(self.signals.history):
                self.processed_count = 0

            # Kiểm tra nếu số tin nhắn mới >= 20 thì tạo memory mới
            if len(self.signals.history) - self.processed_count >= 20:
                print("MEMORY: Generating new memories")

                # Copy the latest unprocessed messages
                messages = copy.deepcopy(self.signals.history[-(len(self.signals.history) - self.processed_count):])

                #[
                    #{"role": "user", "content": "Huy: Hello!\n"},
                    #{"role": "assistant", "content": "UI-chan: Hi there!\n"},
                    #{"role": "user", "content": "Huy: How are you?\n"},
                    #{"role": "assistant", "content": "UI-chan: I'm great!\n"}
                #]
                for message in messages:
                    if message["role"] == "user" and message["content"] != "":
                        message["content"] = HOST_NAME + ": " + message["content"] + "\n"
                    elif message["role"] == "assistant" and message["content"] != "":
                        message["content"] = AI_NAME + ": " + message["content"] + "\n"

                # Huy: Hello!
                # UI-chan: Hi there!
                # Huy: How are you?
                # UI-chan: I'm great!
                chat_section = ""
                for message in messages:
                    chat_section += message["content"]

                chat_input = chat_section + MEMORY_PROMPT
                tokenizer = self.modules["text"].tokenizer
                model = self.modules["text"].model

                inputs = tokenizer(chat_input, return_tensors="pt").to(model.device)

                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=200,
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.9,
                        repetition_penalty=1.1,
                        pad_token_id=tokenizer.eos_token_id
                    )

                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                raw_memories = generated_text[len(chat_input):].strip()
                
                # Split từng phần Q&A và thêm vào memory mới trong db 
                for memory in raw_memories.split("{qa}"):
                    memory = memory.strip()
                    if memory != "":
                        self.collection.upsert([str(uuid.uuid4())], documents=[memory], metadatas=[{"type": "short-term"}])

                self.processed_count = len(self.signals.history)

            await asyncio.sleep(5)

    class API:
        def __init__(self, outer):
            self.outer = outer

        def create_memory(self, data):
            id = str(uuid.uuid4())
            self.outer.collection.upsert(id, documents=data, metadatas={"type": "short-term"})

        def delete_memory(self, id):
            self.outer.collection.delete(id)

        def wipe(self):
            self.outer.chroma_client.reset()
            self.outer.chroma_client.create_collection(name="ui_collection")

        def clear_short_term(self):
            short_term_memories = self.outer.collection.get(where={"type": "short-term"})
            for id in short_term_memories["ids"]:
                self.outer.collection.delete(id)

        def import_json(self, path="./memories/memories.json"):
            with open(path, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    print("Error decoding JSON file")
                    return

            for memory in data["memories"]:
                self.outer.collection.upsert(memory["id"], documents=memory["document"], metadatas=memory["metadata"])

        def export_json(self, path="./memories/memories.json"):
            memories = self.outer.collection.get()

            data = {"memories": []}
            for i in range(len(memories["ids"])):
                data["memories"].append({"id": memories["ids"][i],
                                         "document": memories["documents"][i],
                                        "metadata": memories["metadatas"][i]})

            with open(path, "w") as file:
                json.dump(data, file)

        def get_memories(self, query=""):
            data = [];

            if query == "":
                memories = self.outer.collection.get()
                for i in range(len(memories["ids"])):
                    data.append({"id": memories["ids"][i],
                                 "document": memories["documents"][i],
                                 "metadata": memories["metadatas"][i]})
            else:
                memories = self.outer.collection.query(query_texts=query, n_results=30)
                for i in range(len(memories["ids"][0])):
                    data.append({"id": memories["ids"][0][i],
                                 "document": memories["documents"][0][i],
                                 "metadata": memories["metadatas"][0][i],
                                 "distance": memories["distances"][0][i]})

                # Sort memories bằng key distance
                data = sorted(data, key=lambda x: x["distance"])
            return data