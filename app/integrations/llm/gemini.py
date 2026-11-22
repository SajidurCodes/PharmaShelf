from google import genai
from google.genai import types

from app.core.config import get_settings


class GeminiProvider:
    async def chat_with_tools(
        self,
        question,
        system_prompt,
        declarations,
        run_tool,
        history=(),
    ):
        settings = get_settings()
        contents = []

        for message in history:
            role = "model" if message.role == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=message.content)],
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=question)],
            )
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(function_declarations=declarations)],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

        tool_calls = []

        async with genai.Client(
            api_key=settings.GEMINI_API_KEY.get_secret_value()
        ).aio as client:
            for _ in range(5):
                response = await client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )

                if not response.candidates or not response.candidates[0].content:
                    raise RuntimeError("Gemini returned no answer")

                calls = response.function_calls or []
                if not calls:
                    reply = response.text
                    if not reply:
                        raise RuntimeError("Gemini returned an empty reply")
                    return {"reply": reply, "tool_calls": tool_calls}

                contents.append(response.candidates[0].content)

                results = []
                for call in calls:
                    result = await run_tool(call.name, dict(call.args or {}))
                    tool_calls.append(call.name)
                    results.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                id=call.id,
                                name=call.name,
                                response=result,
                            )
                        )
                    )

                contents.append(types.Content(role="user", parts=results))

        raise RuntimeError("Gemini exceeded the tool-call round limit")