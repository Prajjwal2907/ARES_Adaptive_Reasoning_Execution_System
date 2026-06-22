# import all modules
import os, json, datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
import config
from . import memory
from .client import client
from . import actions

# get system prompt
with open(config.SYSTEM_PROMPT_FILE, "r") as system_prompt_file:
    system_prompt = system_prompt_file.read()

with open(config.MEMORY_EXTRACT_PROMPT, "r") as memory_prompt_file:
    memory_extract_prompt = memory_prompt_file.read()


memory.init_memory(client)
actions.init_action_log()


def extract_store(history, date):
    conversation = []
    conversation.append(f"Date: {date}")
    for hist in history:
        if hist['role'] == 'user':
            message = "User"
        elif hist['role'] == 'model':
            message = 'Ares'
        message = message + ":" + hist["text"] + "\n"
        conversation.append(message)

    prompt = memory_extract_prompt + "".join(conversation)

    extracted_data = client.models.generate_content(model=config.GEMINI_MODEL,
                                                    contents = prompt
                                                    )
    try:
        extracted_json = json.loads(extracted_data.text)
    except:
        print("Error extracting memory...")
        return
    
    for item in extracted_json['profile_updates']:
        memory.update_profile(item['field'], item['val'])

    for item in extracted_json['standing_instructions']:
        memory.store_instruction(item)

    memory.store_episode(extracted_json['episodic_summary'], len(history)//2)

    for item in extracted_json['semantic_facts']:
        memory.store_semantic(item['text'], item['metadata'])

    for item in extracted_json['procedural_facts']:
        memory.store_procedural(item['text'], item['metadata'])


# get existing history for the day
if os.path.exists(config.HIST_JSON):
    with open(config.HIST_JSON, 'r') as hist_f:
        hist_data = json.load(hist_f)
        if not hist_data["date"] == datetime.date.today().isoformat():
            if hist_data['history']:
                extract_store(hist_data['history'], hist_data['date'])
            history = []
        else:
            history = hist_data["history"]
else:
    history = []

# convert history to api readable format (types.Content list)
conv_text_list = []
if history:
    for message in history:
        conv_text = types.Content(
            role = message['role'],
            parts = [types.Part.from_text(text=message['text'])]
        )

        conv_text_list.append(conv_text)

# create chat with api
chat = client.chats.create(model = config.GEMINI_MODEL,
                           history=conv_text_list, 
                           config=types.GenerateContentConfig(system_instruction=system_prompt,
                                                              tools = [actions.ares_tools])
                           )

# function to get response from chat and update history
clean_history = history

def get_response(prompt):
    # build memory context
    context_parts = []

    profile = memory.get_profile()
    if profile:
        profile_str = ", ".join([f"{k} = {v}" for k, v in profile.items() if v])
        if profile_str:
            context_parts.append(f"Profile: {profile_str}")

    instructions = memory.get_instructions()
    if instructions:
        inst_str = " / ".join(instructions)
        context_parts.append(f"Standing Instructions: {inst_str}")

    episodes = memory.get_recent_episodes(3)
    if episodes:
        ep_str = " | ".join([f"{ep[0]}: {ep[1]}" for ep in episodes])
        context_parts.append(f"Recent Activity: {ep_str}")

    recent_conversation = "" 
    for conv in clean_history[-6:]:
        recent_conversation += conv['text']
    relevant = memory.retrieve_memories(prompt, 5, recent_conversation)
    if relevant:
        mem_str = " / ".join([m[0] for m in relevant])
        context_parts.append(f"Relevant Memories: {mem_str}")

    # create full prompt using memory
    if context_parts:
        memory_context = "[MEMORY CONTEXT]\n" + "\n".join(context_parts) + "\n\n[USER MESSAGE]\n"
        full_prompt = memory_context + prompt
    else:
        full_prompt = prompt

    # pass full prompt and get response
    response_object = chat.send_message(full_prompt)
    response = response_object.text
    if response:
        if response.strip() == "IGNORE":
            return None
    
    function_calls = [part for part in response_object.parts if part.function_call]

    if function_calls:
        function_responses = []
        for fc in function_calls:
            result = actions.execute_action(fc.function_call.name, fc.function_call.args)
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.function_call.name,
                    response={"result": result}
                )
            )
        response_object = chat.send_message(function_responses)
        response = response_object.text

    clean_history.append({'role': "user", "text":prompt})
    if response:
        clean_history.append({'role': "model", "text":response})
    
    upd_date = datetime.date.today().isoformat()

    upd_data = {'date':upd_date, 'history':clean_history}
    with open(config.HIST_JSON, 'w') as hist_f:
        json.dump(upd_data, hist_f)
    
    return response

