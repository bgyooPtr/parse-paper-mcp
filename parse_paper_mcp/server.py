"""MCP server for parsing academic papers."""

import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from .parser import PaperParser


# Create MCP server
server = Server("parse-paper-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="parse_paper",
            description=(
                "**[RECOMMENDED]** Parse an academic paper (PDF) and extract text and images. "
                "Text is returned in Markdown format. Images are extracted, compressed, and saved to the output directory. "
                "\n\n**Usage Guidelines:**\n"
                "- **With page ranges** (e.g., pages=[0,1,2]): Keep extract_images=True (default) for better understanding.\n"
                "- **Full document at once**: Set extract_images=False to reduce response size.\n"
                "- **For large papers**: Use pages parameter to process 2-5 pages at a time.\n"
                "\n**Tip**: Use max_chars or save_text_to_file to manage large text responses."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save extracted images (optional, uses temp dir if not specified)",
                    },
                    "quality": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Image quality level (default: medium)",
                        "default": "medium",
                    },
                    "image_format": {
                        "type": "string",
                        "enum": ["jpg", "png"],
                        "description": "Image output format (default: jpg)",
                        "default": "jpg",
                    },
                    "extract_images": {
                        "type": "boolean",
                        "description": "Whether to extract images (default: true)",
                        "default": True,
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "Include base64 encoded images in response (default: false)",
                        "default": False,
                    },
                    "pages": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of page numbers (0-based) to extract. Omit for all pages. Example: [0, 1, 2] for first 3 pages.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return in text. Truncates with warning if exceeded. Recommended: 10000-50000 for large papers.",
                    },
                    "save_text_to_file": {
                        "type": "string",
                        "description": "Path to save full text. If provided, only metadata and preview are returned instead of full text.",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="extract_text_only",
            description=(
                "Extract only text from a PDF paper in Markdown format (no images, no metadata). "
                "\n**⚠️ Note**: Generally prefer `parse_paper` for better analysis. "
                "Only use this tool when:\n"
                "- You need extremely fast text-only extraction\n"
                "- Metadata and image information are completely unnecessary\n"
                "- You're doing a quick text-only preview\n"
                "\nSupports page ranges, character limits, and saving to file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                    "pages": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of page numbers (0-based) to extract. Omit for all pages. Example: [0, 1, 2] for first 3 pages.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return. Text will be truncated with a warning if exceeded. Recommended: 10000-50000 for large papers.",
                    },
                    "save_to_file": {
                        "type": "string",
                        "description": "Path to save full text. If provided, only metadata and preview are returned, avoiding large responses.",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="extract_images_only",
            description=(
                "Extract and compress only images from a PDF paper. "
                "Images are saved to the specified directory with compression applied."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save extracted images (optional)",
                    },
                    "quality": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Image quality level (default: medium)",
                        "default": "medium",
                    },
                    "image_format": {
                        "type": "string",
                        "enum": ["jpg", "png"],
                        "description": "Image output format (default: jpg)",
                        "default": "jpg",
                    },
                    "return_base64": {
                        "type": "boolean",
                        "description": "Include base64 encoded images (default: false)",
                        "default": False,
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="get_paper_metadata",
            description=(
                "Get metadata from a PDF paper including page count, title, author, "
                "file size, and other document properties."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to the PDF file",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "parse_paper":
            return await handle_parse_paper(arguments)
        elif name == "extract_text_only":
            return await handle_extract_text(arguments)
        elif name == "extract_images_only":
            return await handle_extract_images(arguments)
        elif name == "get_paper_metadata":
            return await handle_get_metadata(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


async def handle_parse_paper(arguments: dict) -> list[TextContent]:
    """Handle parse_paper tool call."""
    pdf_path = arguments["pdf_path"]
    output_dir = arguments.get("output_dir")
    quality = arguments.get("quality", "medium")
    image_format = arguments.get("image_format", "jpg")
    extract_images = arguments.get("extract_images", True)
    return_base64 = arguments.get("return_base64", False)
    pages = arguments.get("pages")
    max_chars = arguments.get("max_chars")
    save_text_to_file = arguments.get("save_text_to_file")

    parser = PaperParser(pdf_path)
    result = parser.parse_full(
        output_dir=output_dir,
        quality=quality,
        image_format=image_format,
        extract_images=extract_images,
        return_base64=return_base64,
        pages=pages,
        max_chars=max_chars,
        save_text_to_file=save_text_to_file,
    )

    # Format response
    response = f"# Paper Parsing Complete\n\n"
    response += f"## Metadata\n"
    response += f"- **Title**: {result['metadata'].get('title', 'N/A')}\n"
    response += f"- **Author**: {result['metadata'].get('author', 'N/A')}\n"
    response += f"- **Pages**: {result['metadata']['page_count']}\n"
    response += f"- **File Size**: {result['metadata']['file_size']:,} bytes\n\n"

    if result['images']:
        response += f"## Extracted Images\n"
        response += f"Total images: {len(result['images'])}\n\n"
        for img in result['images']:
            response += f"- **{img['filename']}** (Page {img['page']})\n"
            response += f"  - Path: `{img['path']}`\n"
            response += f"  - Size: {img['width']}x{img['height']} pixels\n"
            response += f"  - File size: {img['file_size']:,} bytes\n"
            if return_base64:
                response += f"  - Base64: Available (length: {len(img['base64'])} chars)\n"
            response += "\n"
    else:
        response += "## Images\nNo images extracted.\n\n"

    response += f"## Text Content\n\n"
    response += result['text']

    # Also return structured data as JSON
    json_data = json.dumps(
        {
            "metadata": result['metadata'],
            "images": result['images'],
            "text_length": len(result['text']),
        },
        indent=2,
    )

    return [
        TextContent(type="text", text=response),
        TextContent(type="text", text=f"\n\n---\n\n**Structured Data (JSON):**\n```json\n{json_data}\n```"),
    ]


async def handle_extract_text(arguments: dict) -> list[TextContent]:
    """Handle extract_text_only tool call."""
    pdf_path = arguments["pdf_path"]
    pages = arguments.get("pages")
    max_chars = arguments.get("max_chars")
    save_to_file = arguments.get("save_to_file")

    parser = PaperParser(pdf_path)
    text = parser.extract_text(
        pages=pages,
        max_chars=max_chars,
        save_to_file=save_to_file,
    )

    return [TextContent(type="text", text=text)]


async def handle_extract_images(arguments: dict) -> list[TextContent]:
    """Handle extract_images_only tool call."""
    pdf_path = arguments["pdf_path"]
    output_dir = arguments.get("output_dir")
    quality = arguments.get("quality", "medium")
    image_format = arguments.get("image_format", "jpg")
    return_base64 = arguments.get("return_base64", False)

    parser = PaperParser(pdf_path)
    images = parser.extract_images(
        output_dir=output_dir,
        quality=quality,
        image_format=image_format,
        return_base64=return_base64,
    )

    response = f"# Image Extraction Complete\n\n"
    response += f"Total images extracted: {len(images)}\n\n"

    for img in images:
        response += f"## {img['filename']}\n"
        response += f"- **Page**: {img['page']}\n"
        response += f"- **Path**: `{img['path']}`\n"
        response += f"- **Dimensions**: {img['width']}x{img['height']} pixels\n"
        response += f"- **File size**: {img['file_size']:,} bytes\n"
        if return_base64:
            response += f"- **Base64**: Available (length: {len(img['base64'])} chars)\n"
        response += "\n"

    # JSON data
    json_data = json.dumps(images, indent=2)

    return [
        TextContent(type="text", text=response),
        TextContent(type="text", text=f"\n\n**JSON Data:**\n```json\n{json_data}\n```"),
    ]


async def handle_get_metadata(arguments: dict) -> list[TextContent]:
    """Handle get_paper_metadata tool call."""
    pdf_path = arguments["pdf_path"]

    parser = PaperParser(pdf_path)
    metadata = parser.get_metadata()

    response = f"# PDF Metadata\n\n"
    response += f"- **Filename**: {metadata['filename']}\n"
    response += f"- **File Size**: {metadata['file_size']:,} bytes ({metadata['file_size'] / 1024 / 1024:.2f} MB)\n"
    response += f"- **Pages**: {metadata['page_count']}\n"
    response += f"- **Title**: {metadata.get('title', 'N/A')}\n"
    response += f"- **Author**: {metadata.get('author', 'N/A')}\n"
    response += f"- **Subject**: {metadata.get('subject', 'N/A')}\n"
    response += f"- **Creator**: {metadata.get('creator', 'N/A')}\n"
    response += f"- **Producer**: {metadata.get('producer', 'N/A')}\n"
    response += f"- **Creation Date**: {metadata.get('creation_date', 'N/A')}\n"
    response += f"- **Modification Date**: {metadata.get('modification_date', 'N/A')}\n"

    json_data = json.dumps(metadata, indent=2)

    return [
        TextContent(type="text", text=response),
        TextContent(type="text", text=f"\n\n**JSON Data:**\n```json\n{json_data}\n```"),
    ]


async def async_main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
