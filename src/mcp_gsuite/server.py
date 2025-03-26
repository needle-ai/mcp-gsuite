
import logging
from collections.abc import Sequence
from typing import Any
import traceback
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from . import tools_gmail
from . import tools_calendar
from . import toolhandler


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite")


app = Server("mcp-gsuite")

tool_handlers = {}
def add_tool_handler(tool_class: toolhandler.ToolHandler):
    global tool_handlers

    tool_handlers[tool_class.name] = tool_class

def get_tool_handler(name: str) -> toolhandler.ToolHandler | None:
    if name not in tool_handlers:
        return None
    
    return tool_handlers[name]

add_tool_handler(tools_gmail.QueryEmailsToolHandler())
add_tool_handler(tools_gmail.GetEmailByIdToolHandler())
add_tool_handler(tools_gmail.CreateDraftToolHandler())
add_tool_handler(tools_gmail.DeleteDraftToolHandler())
add_tool_handler(tools_gmail.ReplyEmailToolHandler())
add_tool_handler(tools_gmail.GetAttachmentToolHandler())
add_tool_handler(tools_gmail.BulkGetEmailsByIdsToolHandler())
add_tool_handler(tools_gmail.BulkSaveAttachmentsToolHandler())

add_tool_handler(tools_calendar.ListCalendarsToolHandler())
add_tool_handler(tools_calendar.GetCalendarEventsToolHandler())
add_tool_handler(tools_calendar.CreateCalendarEventToolHandler())
add_tool_handler(tools_calendar.DeleteCalendarEventToolHandler())

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""

    return [th.get_tool_description() for th in tool_handlers.values()]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    try:        
        if not isinstance(arguments, dict):
            raise RuntimeError("arguments must be dictionary")
        
        if toolhandler.USER_ID_ARG not in arguments:
            raise RuntimeError("user_id argument is missing in dictionary.")

        tool_handler = get_tool_handler(name)
        if not tool_handler:
            raise ValueError(f"Unknown tool: {name}")

        return tool_handler.run_tool(arguments)
    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(f"Error during call_tool: {str(e)}")
        raise RuntimeError(f"Caught Exception. Error: {str(e)}")
