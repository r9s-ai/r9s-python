"""
Response API Examples
Demonstrates various ways to use the R9S Response API (OpenAI 2025 format).

Note: This file uses dict literals for simplicity and readability.
"""
from r9s import R9S
import os


def simple_text_input():
    """Example 1: Simple text input"""
    print("\n" + "="*60)
    print("Example 1: Simple Text Input")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input="Tell me a joke about programming",
            instructions="You are a funny assistant",
            max_output_tokens=500,
            temperature=0.7,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Assistant: {res.output[0].content[0].text}")
        if res.usage:
            print(f"Usage: {res.usage}")


def with_messages():
    """Example 2: Using message array (recommended)"""
    print("\n" + "="*60)
    print("Example 2: Using Message Array")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                },
            ],
            instructions="You are a helpful assistant",
            max_output_tokens=1000,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Assistant: {res.output[0].content[0].text}")


def multi_turn_conversation():
    """Example 3: Multi-turn conversation"""
    print("\n" + "="*60)
    print("Example 3: Multi-turn Conversation")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": "What is artificial intelligence?",
                },
                {
                    "role": "assistant",
                    "content": "Artificial intelligence (AI) is...",
                },
                {
                    "role": "user",
                    "content": "Can you give me some examples?",
                },
            ],
            instructions="You are a knowledgeable AI tutor",
            max_output_tokens=2000,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Assistant: {res.output[0].content[0].text}")


def with_tools():
    """Example 4: Request with tool calls"""
    print("\n" + "="*60)
    print("Example 4: Request with Tool Calls")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": "What's the weather like in San Francisco?",
                },
            ],
            instructions="You are a helpful assistant with access to tools",
            max_output_tokens=2000,
            temperature=0.7,
            tools=[  # type: ignore
                {
                    "type": "function",
                    "name": "get_weather",
                    "description": "Get the current weather in a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string"
                            }
                        },
                        "required": ["location"]
                    }
                }
            ],
            stream=False
        )
        print(f"Output: {res.output}")
        if res.usage:
            print(f"Usage: {res.usage}")


def streaming_response():
    """Example 5: Streaming response"""
    print("\n" + "="*60)
    print("Example 5: Streaming Response")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input="Write a short poem about the ocean",
            instructions="You are a creative poet",
            stream=True,
            max_output_tokens=500,
            temperature=0.9
        )
        print("Assistant: ", end="", flush=True)
        for chunk in res:
            # 只处理文本增量事件
            if chunk.type == "response.output_text.delta":
                print(chunk.delta, end="", flush=True)
        print()  # New line at the end


def json_mode():
    """Example 6: JSON mode output"""
    print("\n" + "="*60)
    print("Example 6: JSON Mode Output")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input="Extract person information and return as JSON: John Smith is 35 years old and works as a software engineer in San Francisco",
            instructions="Extract structured data and output in JSON format",
            text={  # type: ignore
                "format": {
                    "type": "json_object"
                }
            },
            max_output_tokens=500,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"JSON Output:\n{res.output[0].content[0].text}")


def json_schema():
    """Example 7: Structured JSON with schema"""
    print("\n" + "="*60)
    print("Example 7: Structured JSON with Schema")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input="Generate a user profile for software developer Alice Chen in JSON format",
            instructions="Create a detailed user profile following the schema",
            text={  # type: ignore
                "format": {
                    "type": "json_schema",
                    "name": "user_profile",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "age": {
                                "type": "integer"
                            },
                            "occupation": {
                                "type": "string"
                            },
                            "location": {
                                "type": "string"
                            },
                            "skills": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": ["name", "age", "occupation", "location", "skills"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            max_output_tokens=800,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Structured Output:\n{res.output[0].content[0].text}")


def with_metadata():
    """Example 8: Request with metadata"""
    print("\n" + "="*60)
    print("Example 8: Request with Metadata")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-4o-mini",
            input="Summarize the key points from our discussion",
            instructions="You are a meeting assistant",
            max_output_tokens=1500,
            temperature=0.5,
            top_p=0.9,
            metadata={
                "user_id": "user_12345",
                "session_id": "session_abc",
                "conversation_id": "conv_xyz"
            },
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Assistant: {res.output[0].content[0].text}")


def reasoning_mode():
    """Example 9: Reasoning mode for complex problems"""
    print("\n" + "="*60)
    print("Example 9: Reasoning Mode")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.responses.create(
            model="gpt-5-codex",
            input="A farmer needs to transport a fox, a chicken, and a bag of grain across a river. The boat can only carry the farmer and one item. If left alone, the fox will eat the chicken, and the chicken will eat the grain. How can the farmer get everything across safely?",
            instructions="Think through this step by step",
            reasoning={  # type: ignore
                "effort": "high"
            },
            max_output_tokens=3000,
            stream=False
        )
        if res.output and res.output[0].content:
            print(f"Assistant: {res.output[0].content[0].text}")


def main():
    """Run examples with interactive selection"""
    examples = [
        ("Simple Text Input", simple_text_input),
        ("Using Message Array", with_messages),
        ("Multi-turn Conversation", multi_turn_conversation),
        ("Request with Tool Calls", with_tools),
        ("Streaming Response", streaming_response),
        ("JSON Mode Output", json_mode),
        ("Structured JSON with Schema", json_schema),
        ("Request with Metadata", with_metadata),
        ("Reasoning Mode", reasoning_mode),
    ]

    print("\n" + "="*60)
    print("R9S Response API - All Examples")
    print("="*60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nSelect an example to run (1-9), or 0 to run all:")
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
            print("Invalid choice. Running streaming response example...")
            streaming_response()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
