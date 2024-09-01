import mesop as me
from agixtsdk import AGiXTSDK, ChatCompletions
import asyncio

@me.stateclass
class State:
    user_input: str = ""
    agent_response: str = ""
    conversation_name: str = "My Conversation"
    agent_name: str = "gpt4free"
    api_key: str = ""
    base_uri: str = "http://localhost:7437"  # Default base URI
    connection_status: str = "Not connected"

def on_input_change(event: me.InputEvent):
    state = me.state(State)
    state.user_input = event.value

def on_api_key_change(event: me.InputEvent):
    state = me.state(State)
    state.api_key = event.value

def on_base_uri_change(event: me.InputEvent):
    state = me.state(State)
    state.base_uri = event.value

def on_connect(event: me.ClickEvent):
    state = me.state(State)
    try:
        # Attempt to connect to the AGiXT API
        AGiXTSDK(base_uri=state.base_uri, api_key=state.api_key) 
        state.connection_status = "Connected"
    except Exception as e:
        state.connection_status = f"Connection error: {e}"

async def on_send(event: me.ClickEvent):  # Keep on_send asynchronous
    state = me.state(State)
    if state.connection_status != "Connected":
        return  # Don't send if not connected

    # Initialize AGiXTSDK here before using it
    aglxt = AGiXTSDK(base_uri=state.base_uri, api_key=state.api_key)

    user_input = state.user_input
    agent_name = state.agent_name
    conversation_name = state.conversation_name

    # Prepare the chat prompt
    chat_prompt = ChatCompletions(
        model=agent_name,
        messages=[
            {"role": "user", "content": user_input},
        ],
        user=conversation_name,
    )

    def update_state_with_response(response):
        print("API Response (in callback):", response)  # Print for debugging
        state.agent_response = response["choices"][0]["message"]["content"]
        state.user_input = ""

    try:
        # Call chat_completions with the callback function
        await aglxt.chat_completions(prompt=chat_prompt, func=update_state_with_response)
    except Exception as e:
        state.connection_status = f"API Error: {e}"

def on_send_helper(event: me.ClickEvent):  # Helper function to run on_send
    asyncio.run(on_send(event))

def display_conversation(conversation):
    print("Conversation data:", conversation)
    for message in conversation:
        role = message.get("role", "")
        content = message.get("message", "")

        with me.box(style=me.Style(margin="8px", padding="8px", border_radius="4px")):
            if role == "user":
                me.text(f"You: {content}", style=me.Style(color="blue"))
            else:
                if content.startswith("<audio"):
                    me.html(content)
                else:
                    me.text(f"{role}: {content}", style=me.Style(color="green"))

@me.page(path="/")
def index():
    state = me.state(State)

    with me.box(style=me.Style(padding=me.Padding.all("16px"), display="flex", flex_direction="column", height="100vh", 
                                font_family="Roboto, sans-serif", background="#f5f5f5")):  # Corrected padding
        # API Connection Section
        with me.box(style=me.Style(margin=me.Margin(bottom="16px"), padding=me.Padding.all("12px"),  # Corrected padding
                                    border=me.Border.all(me.BorderSide(width=1, color="#ddd")),
                                    border_radius="4px", background="#fff")): 
            me.input(
                label="API Key",
                value=state.api_key,
                on_input=on_api_key_change,
                placeholder="Enter your API key here",
                style=me.Style(width="100%")
            )
            me.input(
                label="Base URI",
                value=state.base_uri,
                on_input=on_base_uri_change,
                placeholder="Enter AGiXT API base URI",
                style=me.Style(width="100%", margin=me.Margin(top="8px")) 
            )
            me.button("Connect", on_click=on_connect, style=me.Style(margin=me.Margin(top="8px"), background="#4CAF50", color="#fff"))
            me.text(state.connection_status, style=me.Style(margin=me.Margin(top="8px")))

        # Conversation Area
        with me.box(style=me.Style(flex="1 1 auto", overflow="auto", padding=me.Padding.all("12px"),  # Corrected padding
                                    border=me.Border.all(me.BorderSide(width=1, color="#ddd")),
                                    border_radius="4px", background="#fff")):
            if state.api_key and state.base_uri:
                aglxt = AGiXTSDK(base_uri=state.base_uri, api_key=state.api_key)
                conversation = aglxt.get_conversation(agent_name=state.agent_name, 
                                                    conversation_name=state.conversation_name)
                display_conversation(conversation)

        # Input Section
        with me.box(style=me.Style(display="flex", gap="8px", margin=me.Margin(top="16px"))): 
            me.input(
                placeholder="Type your message...",
                value=state.user_input,
                on_input=on_input_change,
                style=me.Style(flex="1 1 auto"),
                on_enter=on_send,
            )
            me.button("Send", on_click=on_send_helper, style=me.Style(background="#2196F3", color="#fff")) 