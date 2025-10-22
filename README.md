# Human-Controlled MCP Server 🎮

A Model Context Protocol (MCP) server where **you** are the backend! Claude makes requests, and you respond through a beautiful web interface in real-time.

## What Does This Do?

Instead of connecting Claude to APIs, databases, or automated tools, this MCP server connects Claude to **you**. When Claude needs information, wants to make a decision, or needs human judgment, it sends a request to your web dashboard where you can respond.

## Features

- 🌐 **Web Interface**: Beautiful single-page dashboard to see and respond to Claude's requests
- ⚡ **Real-time**: Requests appear instantly in your browser
- 🎨 **Clean UI**: Modern, responsive interface with no frameworks needed
- 🔧 **Multiple Tools**: Ask questions, request searches, or get decisions from humans
- ⏱️ **Timeout Handling**: Automatic 5-minute timeout for pending requests

## Architecture

```
Claude Desktop
    ↓ (MCP Protocol)
Python MCP Server
    ↓ (HTTP)
Web Interface (You!)
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "human-controlled": {
      "command": "python",
      "args": [
        "/absolute/path/to/human_mcp_server.py"
      ]
    }
  }
}
```

**Important**: Replace `/absolute/path/to/human_mcp_server.py` with the actual full path to the Python file.

### 3. Start the Server

You have two options:

**Option A: Via Claude Desktop** (Recommended)
- Just restart Claude Desktop after configuring
- The server starts automatically when Claude Desktop launches
- Open your browser to http://localhost:5000

**Option B: Standalone Testing**
```bash
python human_mcp_server.py
```
Then connect via Claude Desktop or test with an MCP client.

### 4. Open the Web Interface

Navigate to: **http://localhost:5000**

You'll see the Human MCP Control Panel where you can respond to Claude's requests.

## Usage

### In Claude Desktop

Once configured, Claude will have access to three tools:

1. **ask_human**: Ask you a question
2. **human_search**: Request you to search for information
3. **human_decision**: Ask you to make a decision

### Example Conversation

**You**: "Claude, can you ask me what I want for dinner?"

**Claude**: *Uses ask_human tool*

**[Your Web Interface Shows]**:
```
Tool: ask_human
Parameters:
{
  "question": "What would you like for dinner tonight?",
  "context": "The user asked me to ask them this question."
}
```

**You**: *Type "I'd like pasta with marinara sauce" in the web interface and click Submit*

**Claude**: "Based on your response, you'd like pasta with marinara sauce for dinner tonight!"

## Available Tools

### 1. ask_human
Ask the human operator any question.

**Parameters**:
- `question` (required): The question to ask
- `context` (optional): Additional context

**Example Use**: "What's your email address?" "Do you approve this change?" "What are your thoughts on this approach?"

### 2. human_search
Request the human to search for information.

**Parameters**:
- `query` (required): What to search for
- `sources` (optional): Where to look

**Example Use**: "Can you search for the latest news on AI?" "Look up our company's Q3 revenue numbers"

### 3. human_decision
Ask the human to make a decision.

**Parameters**:
- `decision_needed` (required): What needs to be decided
- `options` (required): Available options
- `recommendation` (optional): AI's recommendation

**Example Use**: "Should we use approach A or B for this feature?" "Which design do you prefer?"

## Technical Details

- **Protocol**: Model Context Protocol (MCP) over stdio
- **Server**: Python with Flask for web interface
- **Transport**: Standard input/output for MCP, HTTP for web UI
- **Timeout**: 5 minutes per request
- **Port**: 5000 (web interface)

## Troubleshooting

### Server won't start
- Check that port 5000 isn't already in use
- Verify Python dependencies are installed: `pip list | grep -E "flask|mcp"`

### Claude can't connect
- Verify the path in `claude_desktop_config.json` is absolute and correct
- Restart Claude Desktop after configuration changes
- Check Claude Desktop logs for errors

### Web interface not accessible
- Make sure the server is running: `lsof -i :5000`
- Try accessing `http://127.0.0.1:5000` instead of `localhost`
- Check your firewall settings

### Requests timing out
- Default timeout is 5 minutes - increase `max_wait` in the code if needed
- Make sure your web interface is open and polling

## Customization

### Change the port
Edit `app.run()` in the code:
```python
app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
```

### Add more tools
Add new tools in the `handle_list_tools()` function following the MCP Tool schema.

### Modify timeout
Change `max_wait` in the `handle_call_tool()` function (currently 300 seconds).

### Customize the UI
Edit the `HTML_TEMPLATE` string - it's a single self-contained HTML file with embedded CSS and JavaScript.

## Security Notes

- This server binds to `0.0.0.0`, making it accessible on your local network
- For localhost-only access, change to `host='127.0.0.1'`
- Add authentication if exposing over a network
- Responses are stored in memory only (not persistent)

## Use Cases

- **Personal Assistant**: Claude asks you about your schedule, preferences, or decisions
- **Research Helper**: Claude requests you to look up information it can't access
- **Code Review**: Claude asks for your approval or input on code changes
- **Creative Collaboration**: Claude asks for your creative input or direction
- **Teaching Tool**: Demonstrate how MCP servers work with manual responses

## Credits

Built with:
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [Flask](https://flask.palletsprojects.com/)
- Vanilla JavaScript (no frameworks!)

## License

MIT License - feel free to modify and use as you wish!
