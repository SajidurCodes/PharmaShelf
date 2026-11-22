from google.genai import types

from app.integrations.llm.gemini import GeminiProvider
from app.modules.chat.prompts import CUSTOMER_SYSTEM_PROMPT
from app.modules.chat.tools import CustomerCatalogTools


CUSTOMER_TOOLS = [
    types.FunctionDeclaration(
        name="search_medicines",
        description="Find medicine catalog matches by name, generic name, or SKU.",
        parameters_json_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
    types.FunctionDeclaration(
        name="check_availability",
        description="Check one exact medicine SKU at a specific branch.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "sku": {"type": "string"},
                "branch_code": {"type": "string"},
            },
            "required": ["sku", "branch_code"],
        },
    ),
]


class CustomerChatService:
    def __init__(self, provider: GeminiProvider, tools: CustomerCatalogTools):
        self.provider = provider
        self.tools = tools

    async def run_tool(self, name: str, args: dict) -> dict:
        if name == "search_medicines":
            query = args.get("query")
            if isinstance(query, str) and query.strip():
                return await self.tools.search_medicines(query)

        if name == "check_availability":
            sku = args.get("sku")
            branch = args.get("branch_code")
            if isinstance(sku, str) and isinstance(branch, str):
                return await self.tools.check_availability(sku.strip(), branch.strip())

        return {"error": "Unknown tool or invalid arguments"}

    async def ask(self, question: str) -> dict:
        return await self.provider.chat_with_tools(
            question=question,
            system_prompt=CUSTOMER_SYSTEM_PROMPT,
            declarations=CUSTOMER_TOOLS,
            run_tool=self.run_tool,
        )