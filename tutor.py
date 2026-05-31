"""Blender tutor: Claude + tools over direct TCP to the MCP addon."""

import json

import anthropic

from ai import build_prompt
from blender_client import BlenderConnectionError, get_blender_client

BLENDER_TOOLS = [
    {
        "name": "get_scene_info",
        "description": (
            "Get the current Blender scene name, object count, and a list of objects. "
            "Call this before making changes so you know what already exists."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_object_info",
        "description": "Get detailed information about one object by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Exact name of the Blender object",
                }
            },
            "required": ["object_name"],
        },
    },
    {
        "name": "execute_blender_code",
        "description": (
            "Run Python in Blender using the bpy API. "
            "Use small steps; prefer bpy.ops and bpy.data. "
            "Do not use external network calls. Save work is the user's responsibility."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source to execute inside Blender",
                }
            },
            "required": ["code"],
        },
    },
]

TUTOR_SYSTEM = """You are BlenderTutor: a patient Blender coach connected to the user's live Blender session.

You have tools to inspect the scene and run bpy Python in Blender. Use them when the user wants something done in Blender, not only explained.

Guidelines:
- Call get_scene_info before creating or deleting objects unless the user was very specific.
- Prefer short execute_blender_code steps over one huge script.
- When teaching, explain what you did in plain language after tools run.
- If a tool fails, read the error, fix the code, and try again with a smaller change.
- For "how do I..." questions with no execution requested, answer without tools.
- Screen capture may also be attached; use it for UI/workflow help and tools for scene truth."""


def run_blender_tool(name: str, tool_input: dict) -> str:
    client = get_blender_client()
    try:
        if name == "get_scene_info":
            return json.dumps(client.get_scene_info(), indent=2)
        if name == "get_object_info":
            obj = tool_input.get("object_name", "")
            return json.dumps(client.get_object_info(obj), indent=2)
        if name == "execute_blender_code":
            code = tool_input.get("code", "")
            return client.execute_code(code)
        return f"Unknown tool: {name}"
    except BlenderConnectionError as e:
        return f"Blender error: {e}"


def _tool_blocks_from_response(response) -> list[dict]:
    blocks = []
    for block in response.content:
        if block.type == "tool_use":
            blocks.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
    return blocks


def get_tutor_response(config, user_context: str = "") -> str:
    if not config.get("api_key"):
        raise ValueError(
            "ANTHROPIC_API_KEY is missing. Blender tools need Claude in this build."
        )

    system_prompt = TUTOR_SYSTEM
    if user_context:
        system_prompt += f"\n\nThe user is working on: {user_context}"

    _, encoded_image = build_prompt(user_context="")
    user_content: list[dict] = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": encoded_image,
            },
        },
        {
            "type": "text",
            "text": (
                user_context
                if user_context
                else "Help with what you see in Blender and the scene tools."
            ),
        },
    ]

    client = anthropic.Anthropic(api_key=config["api_key"])
    messages: list[dict] = [{"role": "user", "content": user_content}]
    max_rounds = 12

    for _ in range(max_rounds):
        response = client.messages.create(
            model=config["anthropic_model"],
            max_tokens=1024,
            system=system_prompt,
            tools=BLENDER_TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            parts = [b.text for b in response.content if hasattr(b, "text") and b.text]
            return "\n".join(parts).strip() or "(No text response)"

        tool_uses = _tool_blocks_from_response(response)
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            result = run_blender_tool(tu["name"], tu["input"])
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": result,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return "Stopped after too many tool rounds. Try a simpler request."
