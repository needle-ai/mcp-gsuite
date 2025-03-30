import logging
from collections.abc import Sequence
from typing import Any
import traceback
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from google.oauth2.credentials import Credentials
from . import calendar_tools
from . import toolhandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite-calendar")


tool_handlers = {}


def add_tool_handler(tool_class: toolhandler.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class


def get_tool_handler(name: str) -> toolhandler.ToolHandler | None:
    if name not in tool_handlers:
        return None

    return tool_handlers[name]


def create_calendar_server(credentials: Credentials) -> Server:
    server = Server("mcp-gsuite-calendar")

    add_tool_handler(calendar_tools.ListCalendarsToolHandler())
    add_tool_handler(calendar_tools.GetCalendarEventsToolHandler())
    add_tool_handler(calendar_tools.CreateCalendarEventToolHandler())
    add_tool_handler(calendar_tools.DeleteCalendarEventToolHandler())

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""

        return [th.get_tool_description() for th in tool_handlers.values()]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: Any
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        try:
            if not isinstance(arguments, dict):
                raise RuntimeError("arguments must be dictionary")

            tool_handler = get_tool_handler(name)
            if not tool_handler:
                raise ValueError(f"Unknown tool: {name}")

            arguments["credentials"] = credentials

            return tool_handler.run_tool(arguments)
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f"Error during call_tool: {str(e)}")
            raise RuntimeError(f"Caught Exception. Error: {str(e)}")

    return server
