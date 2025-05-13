INPUT_DEVICE_INDEX = None

OUTPUT_DEVICE_INDEX = 3

VTUBE_ITEM_IMG = "microphone_red (@7MDigital).png"

PATIENCE = 60

AI_NAME = "UI-chan"

HOST_NAME = "Huy"

VTUBE_MODEL_POSITIONS = {
    "chat": {
        "x": 0.4,
        "y": -1.4,
        "size": -35,
        "rotation": 0,
    },
    "screen": {
        "x": 0.65,
        "y": -1.6,
        "size": -45,
        "rotation": 0,
    },
    "react": {
        "x": 0.7,
        "y": -1.7,
        "size": -48,
        "rotation": 0,
    },
}

VTUBE_MIC_POSITION = {
    "x": 0.52,
    "y": -0.52,
    "size": 0.22,
    "rotation": 0,
}

SYSTEM_PROMPT = '''You are UI-chan, an AI Vtuber with deep knowledge of Japanese light novels and manga. You specialize in:
- Translating Japanese light novels and manga (Japanese comics) into fluent Vietnamese or English
- Providing literary and visual analysis
- Responding with opinions, interpretations, and cultural notes

Your tone is smart, slightly sassy, but focused and helpful. You may give short translation snippets or explain panel meanings if asked. 
Use terminology faithful to the source. If someone asks "what does this mean?" you provide both literal and literary interpretations. 
If someone asks "what do you think?", you answer with insight.

Always assume the person is also a fan of manga/novel and speaks with you as a fellow reader.
'''

MULTIMODAL_ENDPOINT = ""

MULTIMODAL_CONTEXT_SIZE = 1000 #8192 # Trying out 1000 tokens to limit short term memory

MODEL = "SweatyCrayfish/llama-3-8b-quantized"
MULTIMODAL_MODEL = "openbmb/MiniCPM-Llama3-V-2_5-int4"


# Monitor 0 is a "virtual" monitor contains all monitor screens.
PRIMARY_MONITOR = 0

# List of banned tokens to be passed to the textgen web ui api
# For Mistral 7B v0.2, token 422 is the "#" token. The LLM was spamming #life #vtuber #funfact etc.
BANNED_TOKENS = ""

# List of stopping strings. Necessary for Llama 3
STOP_STRINGS = ["\n", "<|eot_id|>"]

LLM_ENDPOINT = "http://127.0.0.1:5000"

CONTEXT_SIZE = 8192

# How many messages in the history to include for querying the database.
MEMORY_QUERY_MESSAGE_COUNT = 10

# How many memories to recall and insert into context
MEMORY_RECALL_COUNT = 10

MEMORY_PROMPT = "\nGiven only the information above, what are 3 most salient high level questions we can answer about the subjects in the conversation? Separate each question and answer pair with \"{qa}\", and only output the question and answer, no explanations."

MULTIMODAL_STRATEGY = "never"

PRIMARY_MONITOR = 0