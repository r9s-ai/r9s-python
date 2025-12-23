"""
Chat Completions API Examples
Demonstrates various ways to use the R9S chat completions API.

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""
from r9s import R9S
import os
import json


def basic_chat():
    """Example 1: Basic chat request"""
    print("\n" + "="*60)
    print("Example 1: Basic Chat")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ]
        )
        print(f"Assistant: {res.choices[0].message.content}")
        print(f"Usage: {res.usage}")


def chat_with_system_prompt():
    """Example 2: Chat with system prompt"""
    print("\n" + "="*60)
    print("Example 2: Chat with System Prompt")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        print(f"Assistant: {res.choices[0].message.content}")


def streaming_chat():
    """Example 3: Streaming chat"""
    print("\n" + "="*60)
    print("Example 3: Streaming Chat")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Tell me a short story about a cat"}
            ],
            stream=True,
            stream_options={"include_usage": True},
            temperature=0.8
        )

        print("Assistant: ", end="", flush=True)
        for chunk in res:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
            if chunk.usage is not None:
                print(f"\n\nUsage: {chunk.usage}")


def chat_with_tools():
    """Example 4: Chat with tool calls"""
    print("\n" + "="*60)
    print("Example 4: Chat with Tool Calls")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        # Define tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit to use"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

        # First request
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What's the weather like in San Francisco?"}
            ],
            tools=tools,  # type: ignore
            tool_choice="auto"
        )

        assistant_message = res.choices[0].message
        print(f"Assistant wants to call: {assistant_message.tool_calls[0].function.name if assistant_message.tool_calls else 'No tool call'}")

        if assistant_message.tool_calls:
            # Simulate tool execution
            tool_call = assistant_message.tool_calls[0]
            tool_response = json.dumps({
                "temperature": 18,
                "condition": "sunny",
                "humidity": 65
            })

            # Second request with tool result
            messages = [
                {"role": "user", "content": "What's the weather in San Francisco?"},
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                },
                {
                    "role": "tool",
                    "content": tool_response,
                    "tool_call_id": tool_call.id
                }
            ]

            final_res = r9_s.chat.create(
                model="gpt-4o-mini",
                messages=messages,  # type: ignore
                tools=tools  # type: ignore
            )
            print(f"Final answer: {final_res.choices[0].message.content}")


def multi_turn_conversation():
    """Example 5: Multi-turn conversation"""
    print("\n" + "="*60)
    print("Example 5: Multi-turn Conversation")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        messages = [
            {"role": "system", "content": "You are a knowledgeable programming tutor."},
            {"role": "user", "content": "How do I create a list in Python?"},
            {"role": "assistant", "content": "In Python, you can create a list using square brackets. For example: my_list = [1, 2, 3]"},
            {"role": "user", "content": "How do I add items to it?"}
        ]

        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=messages,  # type: ignore
            max_tokens=500,
            temperature=0.8
        )
        print(f"Assistant: {res.choices[0].message.content}")


def json_mode_output():
    """Example 6: JSON mode output"""
    print("\n" + "="*60)
    print("Example 6: JSON Mode Output")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs in JSON format."},
                {"role": "user", "content": "Extract the name, age, and occupation from this text: John is 30 years old and works as a software engineer."}
            ],
            response_format={"type": "json_object"},
            temperature=0.5
        )
        print(f"JSON Output:\n{res.choices[0].message.content}")


def structured_json_output():
    """Example 7: Structured JSON output with schema"""
    print("\n" + "="*60)
    print("Example 7: Structured JSON Output with Schema")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Generate a user profile for a software engineer named Alice"}
            ],
            response_format={  # type: ignore
                "type": "json_schema",
                "json_schema": {
                    "name": "user_profile",
                    "description": "A user profile object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"},
                            "occupation": {"type": "string"},
                            "skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "occupation"]
                    }
                }
            },
            temperature=0.7
        )
        print(f"Structured Output:\n{res.choices[0].message.content}")


def vision_input():
    """Example 8: Vision input (image understanding)"""
    print("\n" + "="*60)
    print("Example 8: Vision Input")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        print(f"Assistant: {res.choices[0].message.content}")


def forced_tool_call():
    """Example 9: Forced tool call"""
    print("\n" + "="*60)
    print("Example 9: Forced Tool Call")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get current time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {"type": "string"}
                        }
                    }
                }
            }
        ]

        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Tell me about the weather"}
            ],
            tools=tools,  # type: ignore
            tool_choice={  # type: ignore
                "type": "function",
                "function": {"name": "get_weather"}
            }
        )

        if res.choices[0].message.tool_calls:
            print(f"Forced to call: {res.choices[0].message.tool_calls[0].function.name}")


def parallel_tool_calls():
    """Example 10: Parallel tool calls"""
    print("\n" + "="*60)
    print("Example 10: Parallel Tool Calls")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"}
                        },
                        "required": ["city"]
                    }
                }
            }
        ]

        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Check the weather in Tokyo, Paris, and New York simultaneously"}
            ],
            tools=tools,  # type: ignore
            parallel_tool_calls=True,
            temperature=0.7
        )

        if res.choices[0].message.tool_calls:
            print(f"Number of parallel tool calls: {len(res.choices[0].message.tool_calls)}")
            for i, tool_call in enumerate(res.choices[0].message.tool_calls, 1):
                print(f"  {i}. {tool_call.function.name}({tool_call.function.arguments})")


def with_metadata():
    """Example 11: Request with metadata and user tracking"""
    print("\n" + "="*60)
    print("Example 11: With Metadata and User Tracking")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.chat.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Explain quantum entanglement in simple terms"}
            ],
            temperature=0.8,
            max_tokens=300,
            user="user_abc123",
            metadata={
                "session_id": "session_xyz789",
                "conversation_id": "conv_456",
                "source": "mobile_app",
                "version": "1.2.3"
            },
            store=True
        )
        print(f"Assistant: {res.choices[0].message.content}")


def main():
    """Run all examples"""
    examples = [
        ("Basic Chat", basic_chat),
        ("Chat with System Prompt", chat_with_system_prompt),
        ("Streaming Chat", streaming_chat),
        ("Chat with Tools", chat_with_tools),
        ("Multi-turn Conversation", multi_turn_conversation),
        ("JSON Mode Output", json_mode_output),
        ("Structured JSON Output", structured_json_output),
        ("Vision Input", vision_input),
        ("Forced Tool Call", forced_tool_call),
        ("Parallel Tool Calls", parallel_tool_calls),
        ("With Metadata", with_metadata),
    ]

    print("\n" + "="*60)
    print("R9S Chat Completions API - All Examples")
    print("="*60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nSelect an example to run (1-11), or 0 to run all:")
    try:
        choice = input("Your choice: ").strip()

        if choice == "0":
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\nError in {name}: {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            func()
        else:
            print("Invalid choice. Running basic chat example...")
            basic_chat()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
