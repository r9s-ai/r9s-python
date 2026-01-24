"""
Embeddings API Examples
Demonstrates various ways to use the R9S embeddings API.

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""

from r9s import R9S
import os
import asyncio


def basic_embedding():
    """Example 1: Basic single text embedding"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Single Text Embedding")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input="The food was delicious and the waiter was friendly.",
        )
        print(f"Model: {res.model}")
        print(f"Number of embeddings: {len(res.data)}")
        print(f"Embedding dimension: {len(res.data[0].embedding)}")
        print(f"First 5 values: {res.data[0].embedding[:5]}")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def multiple_embeddings():
    """Example 2: Multiple text embeddings in a single request"""
    print("\n" + "=" * 60)
    print("Example 2: Multiple Text Embeddings")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        texts = [
            "Hello world",
            "Goodbye world",
            "How are you?",
            "Nice to meet you",
        ]

        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )

        print(f"Number of embeddings: {len(res.data)}")
        for i, embedding_obj in enumerate(res.data):
            print(
                f"  [{embedding_obj.index}] Text: '{texts[i][:30]}...' -> dim={len(embedding_obj.embedding)}"
            )
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def embedding_with_base64():
    """Example 3: Embedding with base64 encoding format"""
    print("\n" + "=" * 60)
    print("Example 3: Base64 Encoding Format")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input="Convert this to an embedding.",
            encoding_format="base64",
        )

        embedding = res.data[0].embedding
        if isinstance(embedding, str):
            print("Encoding format: base64")
            print(f"Base64 string length: {len(embedding)}")
            print(f"First 100 characters: {embedding[:100]}...")
        else:
            print("Unexpected format: got list instead of base64 string")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def embedding_with_dimensions():
    """Example 4: Embedding with custom dimensions (text-embedding-3 models only)"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Dimensions")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        # Note: dimensions parameter only works with text-embedding-3-small and text-embedding-3-large
        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input="Reduce the embedding dimensions for efficiency.",
            dimensions=256,
        )

        print(f"Model: {res.model}")
        print("Requested dimensions: 256")
        print(f"Actual embedding dimension: {len(res.data[0].embedding)}")
        print(f"First 5 values: {res.data[0].embedding[:5]}")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def token_input_embedding():
    """Example 5: Embedding with token array input"""
    print("\n" + "=" * 60)
    print("Example 5: Token Array Input")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        # Token IDs for "Hello world" (example tokens, actual IDs depend on tokenizer)
        # These are example token IDs - in practice you'd use a tokenizer to get real IDs
        tokens = [9906, 1917]  # Example token IDs

        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input=tokens,
        )

        print(f"Input tokens: {tokens}")
        print(f"Embedding dimension: {len(res.data[0].embedding)}")
        print(f"First 5 values: {res.data[0].embedding[:5]}")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def embedding_with_user():
    """Example 6: Embedding with user tracking"""
    print("\n" + "=" * 60)
    print("Example 6: With User Tracking")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input="Track this embedding request.",
            user="user_abc123",
        )

        print(f"Model: {res.model}")
        print(f"Embedding dimension: {len(res.data[0].embedding)}")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


async def async_embedding():
    """Example 7: Async embedding request"""
    print("\n" + "=" * 60)
    print("Example 7: Async Embedding")
    print("=" * 60)

    async with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = await r9s.embeddings.create_async(
            model="text-embedding-3-small",
            input="This is an async embedding request.",
        )

        print(f"Model: {res.model}")
        print(f"Embedding dimension: {len(res.data[0].embedding)}")
        print(f"First 5 values: {res.data[0].embedding[:5]}")
        print(
            f"Usage: prompt_tokens={res.usage.prompt_tokens}, total_tokens={res.usage.total_tokens}"
        )


def run_async_example():
    """Wrapper to run async example"""
    asyncio.run(async_embedding())


def semantic_similarity():
    """Example 8: Calculate semantic similarity between texts"""
    print("\n" + "=" * 60)
    print("Example 8: Semantic Similarity")
    print("=" * 60)

    def cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        return dot_product / (magnitude1 * magnitude2)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        texts = [
            "The cat sat on the mat",
            "A kitten was resting on the rug",
            "The stock market crashed today",
        ]

        res = r9s.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )

        embeddings = [obj.embedding for obj in res.data]

        print("Similarity scores:")
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = cosine_similarity(embeddings[i], embeddings[j])
                print(
                    f"  '{texts[i][:30]}...' vs '{texts[j][:30]}...': {similarity:.4f}"
                )


def main():
    """Run all examples"""
    examples = [
        ("Basic Single Text Embedding", basic_embedding),
        ("Multiple Text Embeddings", multiple_embeddings),
        ("Base64 Encoding Format", embedding_with_base64),
        ("Custom Dimensions", embedding_with_dimensions),
        ("Token Array Input", token_input_embedding),
        ("With User Tracking", embedding_with_user),
        ("Async Embedding", run_async_example),
        ("Semantic Similarity", semantic_similarity),
    ]

    print("\n" + "=" * 60)
    print("R9S Embeddings API - All Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print(f"\nSelect an example to run (1-{len(examples)}), or 0 to run all:")
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
            print("Invalid choice. Running basic embedding example...")
            basic_embedding()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
