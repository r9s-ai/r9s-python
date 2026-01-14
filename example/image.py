"""
Image API Examples (Huamedia Server)
Demonstrates various ways to use the R9S image APIs with Huamedia server.

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""

from r9s import R9S
import os
import base64


def image_generation_detailed():
    """Example 1: Image generation with detailed parameters"""
    print("\n" + "=" * 60)
    print("Example 1: Image Generation with Detailed Parameters")
    print("=" * 60)

    output_file = "example1_cat.png"

    with R9S(api_key=os.getenv("R9S_API_KEY", ""), timeout_ms=1000 * 60 * 60) as r9s:
        res = r9s.images.create(
            model="gpt-image-1",
            prompt="A cute cat set on table",
            n=1,
            quality="high",
            size="1024x1024",
        )

        if res.data[0].b64_json:
            image_data = base64.b64decode(res.data[0].b64_json)
            with open(output_file, "wb") as f:
                f.write(image_data)
            print(f"Generated HD image saved to: {output_file}")
            print(f"Base64 length: {len(res.data[0].b64_json)}")

        print(f"Timestamp: {res.created}")


def image_generation_streaming():
    """Example 2: Streaming image generation"""
    print("\n" + "=" * 60)
    print("Example 2: Streaming Image Generation")
    print("=" * 60)

    output_dir = "streaming_generation_output"
    os.makedirs(output_dir, exist_ok=True)

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
    ) as r9s:
        stream = r9s.images.create(
            prompt="A futuristic cityscape at sunset with flying cars",
            model="gpt-image-1",
            stream=True,
            partial_images=2,
            n=1,
            size="1024x1024",
        )

        print("Receiving streaming image generation...")
        chunk_count = 0
        final_image_data = None

        for chunk in stream:  # type: ignore[union-attr]
            chunk_count += 1
            event_data = chunk.data  # type: ignore[union-attr]
            print(f"\nChunk {chunk_count}:")
            print(f"  Model: {event_data.model}")  # type: ignore[union-attr]
            print(f"  Object: {event_data.object}")  # type: ignore[union-attr]

            for img in event_data.data:  # type: ignore[union-attr]
                print(f"  Image {img.index}:")
                if img.progress:
                    print(f"    Progress: {img.progress:.2%}")
                if img.is_final:
                    print("    Status: FINAL")
                    if img.b64_json:
                        final_file = os.path.join(output_dir, "final.png")
                        image_data = base64.b64decode(img.b64_json)
                        with open(final_file, "wb") as f:
                            f.write(image_data)
                        print(f"    Saved: {final_file}")
                        final_image_data = img.b64_json
                else:
                    print("    Status: Partial")
                    if img.b64_json:
                        partial_file = os.path.join(
                            output_dir, f"partial_{chunk_count}.png"
                        )
                        image_data = base64.b64decode(img.b64_json)
                        with open(partial_file, "wb") as f:
                            f.write(image_data)
                        print(f"    Saved: {partial_file}")

            if hasattr(event_data, "usage") and event_data.usage:  # type: ignore[union-attr]
                print(f"  Usage: {event_data.usage}")  # type: ignore[union-attr]

        if final_image_data:
            print("\nFinal image saved successfully")
        else:
            print("\nWarning: No final image received")

        print(f"\nTotal chunks received: {chunk_count}")


def image_generation_url():
    """Example 3: URL output"""
    print("\n" + "=" * 60)
    print("Example 3: URL Output")
    print("=" * 60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9s:
        res = r9s.images.create(
            model="dall-e-2",
            prompt="Minimalist logo of a cloud with a lightning bolt",
            n=1,
            response_format="url",
            size="512x512",
        )

        if res.data[0].url:
            print(f"Generated image URL: {res.data[0].url}")

        if res.data[0].revised_prompt:
            print(f"Revised prompt: {res.data[0].revised_prompt}")


def image_edit_simple():
    """Example 4: Simple image edit"""
    print("\n" + "=" * 60)
    print("Example 4: Simple Image Edit")
    print("=" * 60)

    image_path = "example1_cat.png"
    output_file = "example4_cat.png"
    if not os.path.exists(image_path):
        print(f"Input image not found: {image_path}")
        print("Please generate example1_cat.png first to use as input image.")
        return

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
    ) as r9s:
        with open(image_path, "rb") as image_file:
            res = r9s.images.edit(
                image={  # type: ignore
                    "file_name": "cat.png",
                    "content": image_file,
                    "content_type": "image/png",
                },
                prompt="Add a red hat to the cat",
                model="gpt-image-1",
                n=1,
                size="1024x1024",
            )

        if res.data[0].b64_json:
            image_data = base64.b64decode(res.data[0].b64_json)
            with open(output_file, "wb") as f:
                f.write(image_data)
            print(f"Generated HD image saved to: {output_file}")
            print(f"Base64 length: {len(res.data[0].b64_json)}")

        print(f"Timestamp: {res.created}")


def gpt_image_edit_high_fidelity():
    """Example 5: GPT Image model edit with high fidelity"""
    print("\n" + "=" * 60)
    print("Example 5: GPT Image Edit with High Fidelity")
    print("=" * 60)

    image_path = "example1_cat.png"
    output_file = "example5_cat_edited.png"

    if not os.path.exists(image_path):
        print(f"Input image not found: {image_path}")
        print("Please generate example1_cat.png first to use as input image.")
        return

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
    ) as r9s:
        with open(image_path, "rb") as image_file:
            res = r9s.images.edit(
                image={  # type: ignore
                    "file_name": "cat.png",
                    "content": image_file,
                    "content_type": "image/png",
                },
                prompt="Make the cat look majestic with a crown",
                model="gpt-image-1",
                input_fidelity="high",
                size="1024x1024",
                background="opaque",
                output_format="png",
                quality="low",
            )
            if res.data[0].b64_json:
                image_data = base64.b64decode(res.data[0].b64_json)
                with open(output_file, "wb") as f:
                    f.write(image_data)
                print(f"High fidelity edited image saved to: {output_file}")


def gpt_image_edit_streaming():
    """Example 6: Streaming image edit"""
    print("\n" + "=" * 60)
    print("Example 6: Streaming Image Edit")
    print("=" * 60)

    image_path = "example1_cat.png"
    output_dir = "streaming_edit_output"

    if not os.path.exists(image_path):
        print(f"Input image not found: {image_path}")
        print("Please run Example 1 first to generate the input image.")
        return

    os.makedirs(output_dir, exist_ok=True)

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
    ) as r9s:
        with open(image_path, "rb") as image_file:
            stream = r9s.images.edit(
                image={
                    "file_name": "cat.png",
                    "content": image_file,
                    "content_type": "image/png",
                },
                prompt="Put the cat into a cyberpunk style city",
                model="gpt-image-1",
                stream=True,
                partial_images=2,
                n=1,
            )

            print("Receiving streaming image edits...")
            event_count = 0
            final_image_data = None

            for sse_event in stream:
                event_count += 1
                print(f"\nEvent {event_count}:")
                print(f"  Event type: {sse_event.event}")  # type: ignore[union-attr]

                data = sse_event.data  # type: ignore[union-attr]

                if sse_event.event == "image_edit.partial_image":  # type: ignore[union-attr]
                    print("  Status: Partial image")
                    if hasattr(data, "partial_image_index"):
                        print(f"  Partial image index: {data.partial_image_index}")

                    if hasattr(data, "b64_json") and data.b64_json:
                        partial_file = os.path.join(
                            output_dir, f"partial_{event_count}.png"
                        )
                        image_data = base64.b64decode(data.b64_json)
                        with open(partial_file, "wb") as f:
                            f.write(image_data)
                        print(f"  Saved partial image: {partial_file}")

                elif sse_event.event == "image_edit.completed":  # type: ignore[union-attr]
                    print("  Status: COMPLETED")
                    final_image_data = (
                        data.b64_json if hasattr(data, "b64_json") else None
                    )

                    if hasattr(data, "usage") and data.usage:
                        print(f"  Usage: {data.usage}")

                if hasattr(data, "created_at"):
                    print(f"  Created at: {data.created_at}")
                if hasattr(data, "size"):
                    print(f"  Size: {data.size}")
                if hasattr(data, "quality"):
                    print(f"  Quality: {data.quality}")
                if hasattr(data, "output_format"):
                    print(f"  Format: {data.output_format}")

            if final_image_data:
                final_file = os.path.join(output_dir, "final.png")
                image_data = base64.b64decode(final_image_data)
                with open(final_file, "wb") as f:
                    f.write(image_data)
                print(f"\nFinal image saved to: {final_file}")
            else:
                print("\nWarning: No final image received")

            print(f"\nTotal events received: {event_count}")


def gpt_image_edit_multiple():
    """Example 7: Edit with multiple input images"""
    print("\n" + "=" * 60)
    print("Example 7: Edit with Multiple Input Images")
    print("=" * 60)

    image1_path = "example1_cat.png"
    image2_path = "example4_cat.png"
    output_file = "example7_combined.png"

    if not os.path.exists(image1_path) or not os.path.exists(image2_path):
        print("Input images not found.")
        print("Please run Examples 1 and 4 first to generate the required images.")
        return

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
    ) as r9s:
        with open(image1_path, "rb") as img1, open(image2_path, "rb") as img2:
            res = r9s.images.edit(
                image=[  # type: ignore
                    {
                        "file_name": "original_cat.png",
                        "content": img1,
                        "content_type": "image/png",
                    },
                    {
                        "file_name": "cat_with_hat.png",
                        "content": img2,
                        "content_type": "image/png",
                    },
                ],
                prompt="Create a playful scene showing two cats interacting - one original and one wearing a red hat",
                model="gpt-image-1",
                n=1,
                size="1024x1024",
            )

            if res.data[0].b64_json:
                image_data = base64.b64decode(res.data[0].b64_json)
                with open(output_file, "wb") as f:
                    f.write(image_data)
                print(f"Combined image saved to: {output_file}")

            print(f"Generated {len(res.data)} image(s)")


def main():
    """Run all examples"""
    examples = [
        ("Image Generation with Detailed Parameters", image_generation_detailed),
        ("Streaming Image Generation", image_generation_streaming),
        ("URL Output", image_generation_url),
        ("Simple Image Edit", image_edit_simple),
        ("GPT Image Edit with High Fidelity", gpt_image_edit_high_fidelity),
        ("Streaming Image Edit", gpt_image_edit_streaming),
        ("Edit with Multiple Input Images", gpt_image_edit_multiple),
    ]

    print("\n" + "=" * 60)
    print("R9S Image API - All Examples (Huamedia Server)")
    print("=" * 60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nSelect an example to run (1-7), or 0 to run all:")
    print("Note: Examples 4-7 require running previous examples first.")
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
            print("Invalid choice. Running first example...")
            image_generation_detailed()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
