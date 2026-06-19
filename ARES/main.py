from core import brain

while True:
    prompt = input("You: ")
    if prompt.lower() == "exit":
        break
    response = brain.get_response(prompt)
    if response:
        print("ARES:", response)