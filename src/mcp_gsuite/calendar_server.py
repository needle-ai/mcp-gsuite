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
from .calendar_service import CalendarService
from . import calendar_tools
from . import toolhandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite-calendar")


def create_calendar_server(calendar_service: CalendarService) -> Server:
    server = Server("mcp-gsuite-calendar")

    tool_handlers: dict[str, toolhandler.ToolHandler] = {}

    def add_tool_handler(tool_class: toolhandler.ToolHandler):
        tool_handlers[tool_class.name] = tool_class

    add_tool_handler(calendar_tools.ListCalendarsToolHandler(calendar_service))
    add_tool_handler(calendar_tools.GetCalendarEventsToolHandler(calendar_service))
    add_tool_handler(calendar_tools.CreateCalendarEventToolHandler(calendar_service))
    add_tool_handler(calendar_tools.DeleteCalendarEventToolHandler(calendar_service))

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

            tool_handler = tool_handlers.get(name)
            if not tool_handler:
                raise ValueError(f"Unknown tool: {name}")

            return tool_handler.run_tool(arguments)

        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f"Error during call_tool: {str(e)}")
            raise RuntimeError(f"Caught Exception. Error: {str(e)}")

    return server
