import json
from argparse import ArgumentParser

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.db.session import SessionLocal
from app.modules.chat.dependencies import get_customer_catalog_tools
from app.modules.inventory.dependencies import get_inventory_service
from app.modules.medicines.dependencies import get_medicine_service


mcp = FastMCP(
    "PharmaShelf",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "pharmashelf.onrender.com",
            "pharmashelf.onrender.com:443",
            "127.0.0.1:*",
            "localhost:*",
            "[::1]:*",
        ],
        allowed_origins=[
            "https://pharmashelf.onrender.com",
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
        ],
    ),
)


def catalog_tools(session):
    return get_customer_catalog_tools(
        get_medicine_service(session),
        get_inventory_service(session),
    )


@mcp.tool()
async def search_medicines(query: str) -> dict:
    """Find catalog matches by medicine name, generic name, or SKU."""
    query = query.strip()
    if not 1 <= len(query) <= 200:
        raise ValueError("Enter a search term between 1 and 200 characters.")

    async with SessionLocal() as session:
        return await catalog_tools(session).search_medicines(query)


@mcp.tool()
async def check_availability(sku: str, branch_code: str) -> dict:
    """Check whether one exact medicine SKU is available at a branch."""
    sku = sku.strip()
    branch_code = branch_code.strip()
    if not 1 <= len(sku) <= 64 or not 1 <= len(branch_code) <= 40:
        raise ValueError("Enter a valid medicine SKU and branch code.")

    async with SessionLocal() as session:
        return await catalog_tools(session).check_availability(sku, branch_code)


@mcp.resource("pharmashelf://demo/availability", mime_type="application/json")
async def demo_availability() -> str:
    """Current availability of the demo medicine at branch DEMO-01."""
    result = await check_availability("DEMO-PARA-500", "DEMO-01")
    return json.dumps(result, ensure_ascii=False)


@mcp.prompt()
def availability_lookup(medicine: str, branch_code: str) -> str:
    """Guide a customer through a branch availability lookup."""
    return (
        f"Look up {medicine!r} at branch {branch_code!r}. "
        "Use search_medicines to resolve the SKU. If there are multiple "
        "plausible matches, ask which medicine the customer means. "
        "Then use check_availability and report the returned availability. "
        "If the medicine or branch is unknown, say so."
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
    )
    args = parser.parse_args()
    mcp.run(transport=args.transport)