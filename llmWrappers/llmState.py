class LLMState:
    def __init__(self):
        self.enabled = True
        self.next_cancelled = False

        with open('blacklist.txt', 'r') as file:
            self.blacklist = file.read().splitlines()