import os

# Tests never touch the network or real keys.
os.environ["SATYA_LLM"] = "mock"
