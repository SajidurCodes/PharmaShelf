import asyncio

from fastapi import APIRouter, HTTPException
from google.genai import errors

from app.modules.chat.dependencies import CustomerChatServiceDep
from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.owner import router as owner_router


router = APIRouter(prefix="/chat", tags=["Chat"])
router.include_router(owner_router)



@router.post("", response_model=ChatResponse)
async def chat(data: ChatRequest, service: CustomerChatServiceDep) -> ChatResponse:

    try:

        async with asyncio.timeout(60):
            result = await service.ask(data.content, data.history)

    except TimeoutError:

        raise HTTPException(
            status_code=504,
            detail="The assistant took too long to respond",
        ) from None

    
    except errors.APIError:
        
        raise HTTPException(
            status_code=502,
            detail="The assistant provider could not complete the request",
        ) from None

    return ChatResponse.model_validate(result)


