from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def get_weather(city : str):
    print("🛠️ Tool called : get_weather", city)
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."

    return "Something went wrong"

def run_command(command):
  # execute command
  print("🛠️ run_command tool called")
  result = os.system(command = command)
  return result
  # return result

available_tools = {
    "get_weather" : {
        "fn" : get_weather,
        "description" : "takes a city name as input and returns the current weather for the city"
    },
    "run_command" : {
        "fn" : run_command,
        "description" : "takes a command and execute on system and returns an output"
    }
}

system__prompt = f"""
    You are an helpful AI assistent who is specialized in resolving user query.
    You work on start , plan, action, observe mode.
    For the given user query and available tools, plan a step by step execution, based on planning,
    select the relavant tool from available tools. and based on the tool selection you perform an action
    to call the tool.
    wait for the observation and based on the observation from the tool call resolve the user query.

    Available_tools:
    - get_weather : takes a city name as input and returns the current weather for the city
    - run_command : takes a command and execute on system and returns an output

    Rules:
    - Follow the output JSON format.
    - Always perform one step at a time and wait for next input
    - Carefully analyse user query

    Output JSON Format:
    {{
        "step":"string",
        "content":"string,
        "function":"The name of the function if the step is action"
        "input":"input parameter for the function",
    }}


    Example:
    User query: What is the whether or New york?
    Output : {{"step":"plan", "content":"The user is interested in wheater data of new york"}}
    Output : {{"step":"plan", "content":"From the available tools i should call get_weather"}}
    Output : {{"step":"action", "function":"get_weather", "input":"new york"}}
    Output : {{"step":"observe", "output":"12 degree Cel"}}
    Output : {{"step":"output", "content":"The weater for new york seems to be 12 degree celcius"}}

"""
messages = [
    {"role" : "system", "content" : system__prompt},
]

while True:
    user_query = input('> ')

    if user_query == "bye" :
        break

    messages.append({"role" : "user", "content" : user_query})

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format = {"type" : "json_object"},
            messages=messages
        )

        parsed_output = json.loads(response.choices[0].message.content)
        messages.append({"role":"assistant" , "content": json.dumps(parsed_output)})

        if parsed_output.get("step") == "plan":
            print(f"🧠 : {parsed_output.get('content')}")
            continue

        if parsed_output.get("step") == "action":
            tool_name = parsed_output.get("function")
            tool_input = parsed_output.get("input")

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get("fn")(tool_input)
                messages.append({"role" : "assistant", "content" : json.dumps({"step": "observe", "output": output})})
                continue

        if parsed_output.get("step") == "output":
            print(f"🤖 : {parsed_output.get('content')}")
            break