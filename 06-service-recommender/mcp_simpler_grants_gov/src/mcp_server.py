from mcp.server.fastmcp import FastMCP

mcp = FastMCP("First MCP")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b


@mcp.tool()
def compute_yoom(a: int, b: int) -> int:
    """Computes the yoom value for two numbers"""
    return a * 10 + b


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
