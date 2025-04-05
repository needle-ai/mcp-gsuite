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
from .gmail_service import GmailService
from . import gmail_tools
from . import toolhandler


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite-gmail")

tool_handlers = {}


def add_tool_handler(tool_class: toolhandler.ToolHandler):
    tool_handlers[tool_class.name] = tool_class


def get_tool_handler(name: str) -> toolhandler.ToolHandler | None:
    if name not in tool_handlers:
        return None

    return tool_handlers[name]


def create_gmail_server(gmail_service: GmailService) -> Server:
    server = Server("mcp-gsuite-gmail")

    add_tool_handler(gmail_tools.QueryEmailsToolHandler(gmail_service))
    add_tool_handler(gmail_tools.GetEmailByIdToolHandler(gmail_service))
    add_tool_handler(gmail_tools.CreateDraftToolHandler(gmail_service))
    add_tool_handler(gmail_tools.DeleteDraftToolHandler(gmail_service))
    add_tool_handler(gmail_tools.ReplyEmailToolHandler(gmail_service))
    add_tool_handler(gmail_tools.GetAttachmentToolHandler(gmail_service))
    add_tool_handler(gmail_tools.BulkGetEmailsByIdsToolHandler(gmail_service))
    add_tool_handler(gmail_tools.BulkSaveAttachmentsToolHandler(gmail_service))
    add_tool_handler(gmail_tools.SendEmailToolHandler(gmail_service))

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

    return server
