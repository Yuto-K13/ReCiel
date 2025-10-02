from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.genai.errors import APIError
from google.genai.types import Content, Part

from . import errors


class AgentModel:
    gemini_2_5_flash = "gemini-2.5-flash"


async def is_session_active(
    session_service: BaseSessionService,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
) -> bool:
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    return session is not None


async def run_agent(
    session_service: BaseSessionService,
    runner: Runner,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    query: str,
) -> str:
    content = Content(role="user", parts=[Part(text=query)])
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if not await is_session_active(session_service, app_name=app_name, user_id=user_id, session_id=session_id):
                raise errors.MissingSessionError
            if event.is_final_response() and event.content and event.content.parts:
                if event.content.parts[0].text is not None:
                    return event.content.parts[0].text
                break
    except APIError as e:
        raise errors.GoogleADKError from e
    raise errors.GoogleADKError("No Information Returned")
