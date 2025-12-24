"""
Completions API Examples
Demonstrates various ways to use the R9S completions API.

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.

"""

from r9s import R9S
import os


def basic_completion():
    """Example 1: Basic text completion"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Text Completion")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini", prompt="Once upon a time", max_tokens=50
        )
        print(f"Prompt: Once upon a time")
        print(f"Completion: {res.choices[0].text}")
        print(f"Usage: {res.usage}")


def completion_with_options():
    """Example 2: Completion with temperature and other options"""
    print("\n" + "=" * 60)
    print("Example 2: Completion with Options")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="Write a haiku about coding",
            max_tokens=100,
            temperature=0.8,
            top_p=1.0,
            n=1,
        )
        print(f"Completion: {res.choices[0].text}")
        print(f"Finish reason: {res.choices[0].finish_reason}")


def streaming_completion():
    """Example 3: Streaming text completion"""
    print("\n" + "=" * 60)
    print("Example 3: Streaming Completion")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="List 3 benefits of unit testing:\n1.",
            max_tokens=150,
            stream=True,
            stop=["\n\n"],
        )

        print("Completion: ", end="", flush=True)
        for chunk in res:
            if chunk.choices and chunk.choices[0].text:
                print(chunk.choices[0].text, end="", flush=True)


def code_completion():
    """Example 4: Code completion"""
    print("\n" + "=" * 60)
    print("Example 4: Code Completion")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        code_prompt = "def fibonacci(n):"
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt=code_prompt,
            max_tokens=80,
            temperature=0.3,
        )
        print(f"Code prompt:\n{code_prompt}")
        print(f"\nCompletion:\n{res.choices[0].text}")


def completion_with_stop_sequences():
    """Example 5: Completion with stop sequences"""
    print("\n" + "=" * 60)
    print("Example 5: Completion with Stop Sequences")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="Write a Python function to check if a number is prime:\n\n```python\n",
            max_tokens=200,
            temperature=0.5,
            stop=["```", "\n\n\n"],
        )
        print(f"Completion:\n```python\n{res.choices[0].text}")


def multiple_completions():
    """Example 6: Generate multiple completions"""
    print("\n" + "=" * 60)
    print("Example 6: Multiple Completions")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="The best programming language is",
            max_tokens=30,
            temperature=0.9,
            n=3,
        )
        print(f"Generated {len(res.choices)} completions:")
        for i, choice in enumerate(res.choices, 1):
            print(f"\n{i}. {choice.text}")


def completion_with_echo():
    """Example 7: Completion with echo (return prompt)"""
    print("\n" + "=" * 60)
    print("Example 7: Completion with Echo")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="The capital of France is",
            max_tokens=20,
            echo=True,
            temperature=0.3,
        )
        print(f"Full text (with prompt): {res.choices[0].text}")


def completion_with_penalties():
    """Example 8: Completion with frequency and presence penalties"""
    print("\n" + "=" * 60)
    print("Example 8: Completion with Penalties")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        res = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt="Write three creative ways to say hello:",
            max_tokens=100,
            temperature=0.8,
            frequency_penalty=0.5,
            presence_penalty=0.5,
        )
        print(f"Completion: {res.choices[0].text}")


def completion_with_seed():
    """Example 9: Completion with seed for reproducibility"""
    print("\n" + "=" * 60)
    print("Example 9: Completion with Seed (Reproducible)")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        seed = 42
        prompt = "Random number between 1 and 100:"

        # First call
        res1 = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt=prompt,
            max_tokens=20,
            seed=seed,
            temperature=0.7,
        )

        # Second call with same seed
        res2 = r9_s.completions.create(
            model="gpt-4o-mini",
            prompt=prompt,
            max_tokens=20,
            seed=seed,
            temperature=0.7,
        )

        print(f"First call:  {res1.choices[0].text}")
        print(f"Second call: {res2.choices[0].text}")
        print(f"Results match: {res1.choices[0].text == res2.choices[0].text}")


def main():
    """Run all examples"""
    examples = [
        ("Basic Completion", basic_completion),
        ("Completion with Options", completion_with_options),
        ("Streaming Completion", streaming_completion),
        ("Code Completion", code_completion),
        ("Completion with Stop Sequences", completion_with_stop_sequences),
        ("Multiple Completions", multiple_completions),
        ("Completion with Echo", completion_with_echo),
        ("Completion with Penalties", completion_with_penalties),
        ("Completion with Seed", completion_with_seed),
    ]

    print("\n" + "=" * 60)
    print("R9S Completions API - All Examples")
    print("=" * 60)
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
            print("Invalid choice. Running basic completion example...")
            basic_completion()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
