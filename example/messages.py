"""
Messages API Examples
Demonstrates various ways to use the R9S Messages API (Claude/Anthropic compatible).

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""

from r9s import R9S
import os
import json


def basic_message():
    """Example 1: Basic message request"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Message")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hello! How can you assist me today?"}
                    ],
                }
            ],
            max_tokens=1024,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore
        print(
            f"Usage: input_tokens={res.usage.input_tokens}, output_tokens={res.usage.output_tokens}"
        )


def message_with_system_prompt():
    """Example 2: Message with system prompt"""
    print("\n" + "=" * 60)
    print("Example 2: Message with System Prompt")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            system="You are a knowledgeable historian specializing in ancient civilizations.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Tell me about the pyramids of Egypt."}
                    ],
                }
            ],
            max_tokens=500,
            temperature=0.7,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore


def streaming_message():
    """Example 3: Streaming message"""
    print("\n" + "=" * 60)
    print("Example 3: Streaming Message")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Write a short poem about the ocean."}
                    ],
                }
            ],
            max_tokens=300,
            stream=True,
        )

        print("Assistant: ", end="", flush=True)
        for chunk in res:
            # Use TYPE (uppercase) since Speakeasy generates it that way
            chunk_type = getattr(chunk, "TYPE", getattr(chunk, "type", None))  # type: ignore
            if chunk_type == "content_block_delta":
                if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):  # type: ignore
                    print(chunk.delta.text, end="", flush=True)  # type: ignore
            elif chunk_type == "message_stop":
                print("\n")


def message_with_tools():
    """Example 4: Message with tool use"""
    print("\n" + "=" * 60)
    print("Example 4: Message with Tool Use")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        # Define tools
        tools = [
            {
                "name": "get_stock_price",
                "description": "Get the current stock price for a given ticker symbol",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol, e.g. AAPL for Apple",
                        }
                    },
                    "required": ["ticker"],
                },
            }
        ]

        # First request
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's the current stock price of Apple?",
                        }
                    ],
                }
            ],
            tools=tools,  # type: ignore
            max_tokens=1024,
        )

        # Check if tool was called
        tool_use_block = None
        for block in res.content:
            block_type = getattr(block, "TYPE", getattr(block, "type", None))  # type: ignore
            if block_type == "tool_use":
                tool_use_block = block
                print(f"Assistant wants to call: {block.name}")  # type: ignore
                print(f"Arguments: {block.input}")  # type: ignore
                break

        if tool_use_block:
            # Simulate tool execution
            tool_result = json.dumps(
                {
                    "ticker": "AAPL",
                    "price": 178.50,
                    "currency": "USD",
                    "timestamp": "2025-12-23T10:30:00Z",
                }
            )

            # Second request with tool result
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's the current stock price of Apple?",
                        }
                    ],
                },
                {"role": "assistant", "content": res.content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,  # type: ignore
                            "content": tool_result,
                        }
                    ],
                },
            ]

            final_res = r9s.messages.create(
                model="claude-haiku-4.5",
                messages=messages,  # type: ignore
                tools=tools,  # type: ignore
                max_tokens=1024,
            )
            print(f"Final answer: {final_res.content[0].text}")  # type: ignore


def multi_turn_conversation():
    """Example 5: Multi-turn conversation"""
    print("\n" + "=" * 60)
    print("Example 5: Multi-turn Conversation")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "I'm learning Python. Can you explain what a dictionary is?",
                    }
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "A dictionary in Python is a data structure that stores key-value pairs. It's like a real dictionary where you look up a word (key) to find its definition (value).",
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Can you show me an example of creating one?",
                    }
                ],
            },
        ]

        res = r9s.messages.create(
            model="claude-haiku-4.5",
            system="You are a patient Python programming tutor.",
            messages=messages,  # type: ignore
            max_tokens=800,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore


def vision_input():
    """Example 6: Vision input (image understanding)"""
    print("\n" + "=" * 60)
    print("Example 6: Vision Input")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-sonnet-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's in this image? Describe it in detail.",
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore


def base64_image_input():
    """Example 7: Base64 encoded image input"""
    print("\n" + "=" * 60)
    print("Example 7: Base64 Image Input")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        # Example with a small base64 encoded image (you would replace this with actual image data)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        res = r9s.messages.create(
            model="claude-sonnet-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image."},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore


def with_metadata():
    """Example 8: Request with metadata tracking"""
    print("\n" + "=" * 60)
    print("Example 8: With Metadata Tracking")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "What is machine learning?"}],
                }
            ],
            max_tokens=500,
            metadata={
                "user_id": "user_12345",
                "session_id": "session_abc789",
                "source": "web_app",
                "version": "2.1.0",
            },
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore
        print(f"Request ID: {res.id}")


def with_stop_sequences():
    """Example 9: Using stop sequences"""
    print("\n" + "=" * 60)
    print("Example 9: Using Stop Sequences")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {"role": "user", "content": [{"type": "text", "text": "count 1 to 10"}]}
            ],
            max_tokens=200,
            temperature=0.9,
            stop_sequences=["5\n"],
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore
        print(f"Stop reason: {res.stop_reason}")


def temperature_comparison():
    """Example 10: Comparing different temperature settings"""
    print("\n" + "=" * 60)
    print("Example 10: Temperature Comparison")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        prompt = "Write a creative name for a coffee shop."

        # Low temperature (more deterministic)
        print("\nWith temperature=0.0 (deterministic):")
        res1 = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            max_tokens=100,
            temperature=0.0,
        )
        print(f"Response: {res1.content[0].text}")  # type: ignore

        # High temperature (more creative)
        print("\nWith temperature=1.0 (creative):")
        res2 = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            max_tokens=100,
            temperature=1.0,
        )
        print(f"Response: {res2.content[0].text}")  # type: ignore


def top_k_top_p_sampling():
    """Example 11: Using top_k and top_p sampling"""
    print("\n" + "=" * 60)
    print("Example 11: Top-K and Top-P Sampling")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Generate a creative story opening sentence.",
                        }
                    ],
                }
            ],
            max_tokens=150,
            top_k=50,
            top_p=0.95,
        )
        print(f"Assistant: {res.content[0].text}")  # type: ignore


def parallel_tool_calls():
    """Example 12: Multiple tool calls in one turn"""
    print("\n" + "=" * 60)
    print("Example 12: Parallel Tool Calls")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        tools = [
            {
                "name": "get_weather",
                "description": "Get weather for a city",
                "input_schema": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
            {
                "name": "get_time",
                "description": "Get current time in a timezone",
                "input_schema": {
                    "type": "object",
                    "properties": {"timezone": {"type": "string"}},
                    "required": ["timezone"],
                },
            },
        ]

        res = r9s.messages.create(
            model="claude-haiku-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's the weather in Tokyo and what time is it there?",
                        }
                    ],
                }
            ],
            tools=tools,  # type: ignore
            max_tokens=1024,
        )

        tool_calls = [
            block
            for block in res.content
            if getattr(block, "TYPE", getattr(block, "type", None)) == "tool_use"
        ]  # type: ignore
        print(f"Number of tool calls: {len(tool_calls)}")
        for i, tool_call in enumerate(tool_calls, 1):
            print(f"  {i}. {tool_call.name}({tool_call.input})")  # type: ignore


def thinking_mode():
    """Example 13: Extended thinking for complex reasoning"""
    print("\n" + "=" * 60)
    print("Example 13: Extended Thinking Mode")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.messages.create(
            model="claude-sonnet-4.5",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Solve this puzzle: If 5 cats can catch 5 mice in 5 minutes, how many cats are needed to catch 100 mice in 100 minutes?",
                        }
                    ],
                }
            ],
            max_tokens=2000,
            thinking={"type": "enabled", "budget_tokens": 1000},
        )

        # Display thinking process and answer
        for block in res.content:
            block_type = getattr(block, "TYPE", getattr(block, "type", None))  # type: ignore
            if block_type == "thinking":
                print(f"Thinking process:\n{block.thinking}\n")  # type: ignore
            elif block_type == "text":
                print(f"Answer: {block.text}")  # type: ignore


def main():
    """Run all examples"""
    examples = [
        ("Basic Message", basic_message),
        ("Message with System Prompt", message_with_system_prompt),
        ("Streaming Message", streaming_message),
        ("Message with Tools", message_with_tools),
        ("Multi-turn Conversation", multi_turn_conversation),
        ("Vision Input", vision_input),
        ("Base64 Image Input", base64_image_input),
        ("With Metadata", with_metadata),
        ("With Stop Sequences", with_stop_sequences),
        ("Temperature Comparison", temperature_comparison),
        ("Top-K and Top-P Sampling", top_k_top_p_sampling),
        ("Parallel Tool Calls", parallel_tool_calls),
        ("Thinking Mode", thinking_mode),
    ]

    print("\n" + "=" * 60)
    print("R9S Messages API - All Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nSelect an example to run (1-13), or 0 to run all:")
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
            print("Invalid choice. Running basic message example...")
            basic_message()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
