# Parse Paper MCP

A Model Context Protocol (MCP) server for parsing large academic papers (PDF files) with optimized text and image extraction for LLM consumption.

## Features

- Extract text in Markdown format optimized for LLMs
- Extract and compress images with configurable quality levels
- Smart compression: 85%+ size reduction while maintaining readability
- Support for page-by-page extraction
- Rich PDF metadata extraction

## Installation for Claude Code

### Using uvx (Recommended)

Add to your `.mcp.json` file:

```json
{
  "mcpServers": {
    "parse-paper-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/bgyooPtr/parse-paper-mcp", "parse-paper-mcp"]
    }
  }
}
```

Restart Claude Code to load the server.

### Local Development

- Claude Code
```bash
claude mcp add parse-paper-mcp -s project -- uvx  --from git+https://github.com/bgyooPtr/parse-paper-mcp parse-paper-mcp
```

## Available Tools

### `parse_paper`
Parse entire paper with text and images. Use `pages` parameter to process specific pages (e.g., `[0,1,2]` for first 3 pages).

**Key Parameters:**
- `pdf_path` (required): Path to PDF file
- `output_dir` (optional): Directory to save images
- `quality` (optional): `"high"`, `"medium"` (default), `"low"`
- `extract_images` (optional): Whether to extract images (default: true)
- `pages` (optional): List of page numbers to extract (0-based)
- `max_chars` (optional): Limit text length

### `extract_text_only`
Fast text-only extraction in Markdown format (no images).

### `extract_images_only`
Extract and compress only images from PDF.

### `get_paper_metadata`
Get PDF metadata (title, author, page count, file size, etc.).

## Usage in Claude Code

```
Parse /path/to/paper.pdf with medium quality, saving images to /tmp/output
```

```
Extract text from /path/to/paper.pdf pages 0-5
```

```
Get metadata for /path/to/paper.pdf
```

## Quality Levels

- **High**: 1500px max, 90 quality, 200 DPI - Best for detailed diagrams
- **Medium** (Default): 1024px max, 85 quality, 150 DPI - Balanced quality/size
- **Low**: 768px max, 75 quality, 100 DPI - Maximum compression

## License

MIT
