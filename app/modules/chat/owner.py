import asyncio
import json
import re
from urllib.error import URLError

from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors
from pydantic import BaseModel
import httpx2
from app.db.session import SessionDep
from app.integrations.llm.gemini import GeminiProvider
from app.modules.almanac.retrieval import retrieve_passages
from app.modules.auth.dependencies import require_admin
from app.modules.chat.schemas import ChatRequest


router = APIRouter()


NO_MATCH = "I couldn’t find a relevant Almanac entry to answer that question."


class AlmanacSource(BaseModel):
    number: int
    slug: str
    title: str
    source_note: str



class OwnerChatResponse(BaseModel):

    reply: str
    sources: list[AlmanacSource]


def retrieval_question(data: ChatRequest) -> str:
    
    follow_up = re.match(
        r"^(and\b|what about\b|how about\b|why is that\b|why so\b|"
        r"why[?!.]*$|tell me more\b|explain that\b)",
        data.content,
        flags=re.IGNORECASE,
    )


    if follow_up:
        for message in reversed(data.history):
            if message.role == "user":
                return f"{message.content}\nFollow-up: {data.content}"
            
    return data.content




async def answer_owner(data: ChatRequest, session) -> OwnerChatResponse:

    question = retrieval_question(data)

    try:
        passages = await retrieve_passages(session, question)
    except TimeoutError:
        raise
    except (URLError, OSError, ValueError) as exc:
        raise HTTPException(503, "Almanac embeddings are unavailable") from exc

    if not passages:
        return OwnerChatResponse(reply=NO_MATCH, sources=[])

    evidence = [
        {
            "number": number,
            "title": passage.title,
            "passage": passage.content,
            "source_note": passage.source_note,
        }
        for number, passage in enumerate(passages, start=1)
    ]


    try:
        reply = await GeminiProvider().answer_from_passages(
            question, json.dumps(evidence, ensure_ascii=False)
        )



    except httpx2.TimeoutException as exc:
        raise HTTPException(504, "Gemini took too long to respond") from exc
    except httpx2.TransportError as exc:
        raise HTTPException(503, "Could not reach Gemini. Please try again.") from exc
    except (errors.APIError, RuntimeError) as exc:
        raise HTTPException(502, "The assistant could not produce an answer") from exc

    if reply == "NO_ALMANAC_ANSWER":
        return OwnerChatResponse(reply=NO_MATCH, sources=[])

    cited = sorted({int(value) for value in re.findall(r"\[(\d+)\]", reply)})
    if not cited or any(number < 1 or number > len(passages) for number in cited):
        raise HTTPException(502, "The assistant returned an answer without valid citations")

    

    sources = [
        AlmanacSource(
            number=number,
            slug=passages[number - 1].slug,
            title=passages[number - 1].title,
            source_note=passages[number - 1].source_note,
        )
        for number in cited
    ]
    return OwnerChatResponse(reply=reply, sources=sources)





@router.post("/owner",response_model=OwnerChatResponse,dependencies=[Depends(require_admin)],)
async def owner_chat(data: ChatRequest, session: SessionDep) -> OwnerChatResponse:
    try:
        async with asyncio.timeout(60):
            return await answer_owner(data, session)
    except TimeoutError:
        raise HTTPException(504, "The assistant took too long to respond") from None