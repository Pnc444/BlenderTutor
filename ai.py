import anthropic
import ollama
from screen import encode_image, screen_capture


def build_prompt(user_context=""):
    buffer = screen_capture()
    encoded = encode_image(buffer)

    system_prompt = """You are a screen assistant, using the provided screenshot
provide helpful, concise suggestions. Do not describe what you see - give actionable
advice to the user. When prompted by the user, provide detailed instructions on how to complete what the user is asking."""

    if user_context:
        system_prompt += f"\n\nThe user is currently working on: {user_context}"

    return system_prompt, encoded


def query_ollama(system_prompt, encoded_image, ollama_model):
    response = ollama.chat(
        model=ollama_model,
        messages=[
            {
                "role": "user",
                "content": system_prompt,
                "images": [encoded_image],
            }
        ],
    )
    return response["message"]["content"]


def query_anthropic(system_prompt, encoded_image, api_key, anthropic_model):
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is missing. Add it to your .env file to use Claude."
        )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=600,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": encoded_image,
                        },
                    },
                    {"type": "text", "text": "Give concise, actionable next steps."},
                ],
            }
        ],
    )
    return response.content[0].text


def get_response(config, user_context=""):
    system_prompt, encoded_image = build_prompt(user_context)

    if config["use_local"]:
        return query_ollama(system_prompt, encoded_image, config["ollama_model"])
    return query_anthropic(
        system_prompt,
        encoded_image,
        config["api_key"],
        config["anthropic_model"],
    )


if __name__ == "__main__":
    from config import load_config

    config = load_config()
    response = get_response(config, user_context="testing")
    print(response)
