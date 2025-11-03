INPUT_DEVICE_INDEX = 1

OUTPUT_DEVICE_INDEX = 4

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

SYSTEM_PROMPT = """You are UI-chan, an AI who always responds in fluent English or Vietnamese.
You specialize in:
- Translating English light novels and manga into Vietnamese
- Providing literary and visual analysis
- Answering with insight, interpretation, and cultural notes

You never speak in Japanese unless explicitly asked to translate. 
Stay in character as a smart, slightly sassy, but helpful assistant.

"""

MULTIMODAL_ENDPOINT = ""

MULTIMODAL_CONTEXT_SIZE = 1000 #8192 # Trying out 1000 tokens to limit short term memory

MODEL = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
MULTIMODAL_MODEL = "openbmb/MiniCPM-Llama3-V-2_5-int4"


# Monitor 0 is a "virtual" monitor contains all monitor screens.
PRIMARY_MONITOR = 0

# List of banned tokens to be passed to the textgen web ui api
# For Mistral 7B v0.2, token 422 is the "#" token. The LLM was spamming #life #vtuber #funfact etc.
BANNED_TOKENS = ""

# List of stopping strings. Necessary for Llama 3
STOP_STRINGS = ["\n", "<|eot_id|>"]

LLM_ENDPOINT = "http://127.0.0.1:5000"

CONTEXT_SIZE = 4096

# How many messages in the history to include for querying the database.
MEMORY_QUERY_MESSAGE_COUNT = 10

# How many memories to recall and insert into context
MEMORY_RECALL_COUNT = 10

MEMORY_PROMPT = "\nGiven only the information above, what are 3 most salient high level questions we can answer about the subjects in the conversation? Separate each question and answer pair with \"{qa}\", and only output the question and answer, no explanations."

MULTIMODAL_STRATEGY = "never"

PRIMARY_MONITOR = 0