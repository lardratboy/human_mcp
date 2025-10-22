#!/usr/bin/env python3
"""
Human-Controlled MCP Server
A Model Context Protocol server where a human responds to tool calls via a web interface.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Thread
import uuid

from flask import Flask, render_template_string, request, jsonify
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global request queue and responses
pending_requests: Dict[str, Dict[str, Any]] = {}
completed_responses: Dict[str, Any] = {}

# Flask app for web interface
app = Flask(__name__)

# HTML template (single file as requested)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human MCP Control Panel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .status-bar {
            background: white;
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .badge-pending {
            background: #fbbf24;
            color: #78350f;
        }
        
        .badge-completed {
            background: #34d399;
            color: #065f46;
        }
        
        .requests-container {
            display: grid;
            gap: 20px;
        }
        
        .request-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .request-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f3f4f6;
        }
        
        .request-title {
            font-size: 1.3em;
            color: #1f2937;
            font-weight: 600;
        }
        
        .request-time {
            color: #6b7280;
            font-size: 0.9em;
        }
        
        .request-details {
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-family: "Courier New", monospace;
            font-size: 0.9em;
        }
        
        .detail-row {
            margin-bottom: 10px;
        }
        
        .detail-label {
            color: #667eea;
            font-weight: 600;
            display: inline-block;
            width: 100px;
        }
        
        .detail-value {
            color: #374151;
        }
        
        .params-json {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin-top: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .response-section {
            margin-top: 20px;
        }
        
        .response-section label {
            display: block;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        textarea {
            width: 100%;
            min-height: 150px;
            padding: 15px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 1em;
            resize: vertical;
            transition: border-color 0.2s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-submit {
            background: #667eea;
            color: white;
            flex: 1;
        }
        
        .btn-submit:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
        }
        
        .btn-error {
            background: #ef4444;
            color: white;
            flex: 1;
        }
        
        .btn-error:hover {
            background: #dc2626;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3);
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .empty-state-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .empty-state-text {
            color: #6b7280;
            font-size: 1.2em;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            display: none;
            animation: slideInRight 0.3s ease-out;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
            }
            to {
                transform: translateX(0);
            }
        }
        
        .notification.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="notification" id="notification"></div>
    
    <div class="container">
        <h1>🎮 Human MCP Control Panel</h1>
        <p class="subtitle">Respond to Claude's requests in real-time</p>
        
        <div class="status-bar">
            <div class="status-item">
                <span>Pending Requests:</span>
                <span class="status-badge badge-pending" id="pendingCount">0</span>
            </div>
            <div class="status-item">
                <span>Completed:</span>
                <span class="status-badge badge-completed" id="completedCount">0</span>
            </div>
        </div>
        
        <div class="requests-container" id="requestsContainer">
            <div class="empty-state">
                <div class="empty-state-icon">⏳</div>
                <div class="empty-state-text">Waiting for Claude to make a request...</div>
            </div>
        </div>
    </div>
    
    <script>
        let pendingCount = 0;
        let completedCount = 0;
        
        function showNotification(message) {
            const notif = document.getElementById('notification');
            notif.textContent = message;
            notif.classList.add('show');
            setTimeout(() => {
                notif.classList.remove('show');
            }, 3000);
        }
        
        function updateCounts() {
            document.getElementById('pendingCount').textContent = pendingCount;
            document.getElementById('completedCount').textContent = completedCount;
        }
        
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        }
        
        function renderRequests(requests) {
            const container = document.getElementById('requestsContainer');
            
            if (Object.keys(requests).length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⏳</div>
                        <div class="empty-state-text">Waiting for Claude to make a request...</div>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = '';
            
            for (const [requestId, reqData] of Object.entries(requests)) {
                const card = document.createElement('div');
                card.className = 'request-card';
                card.innerHTML = `
                    <div class="request-header">
                        <div class="request-title">🔧 ${reqData.tool_name}</div>
                        <div class="request-time">${formatTime(reqData.timestamp)}</div>
                    </div>
                    
                    <div class="request-details">
                        <div class="detail-row">
                            <span class="detail-label">Request ID:</span>
                            <span class="detail-value">${requestId}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Tool:</span>
                            <span class="detail-value">${reqData.tool_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Parameters:</span>
                        </div>
                        <div class="params-json">${JSON.stringify(reqData.arguments, null, 2)}</div>
                    </div>
                    
                    <div class="response-section">
                        <label for="response-${requestId}">Your Response:</label>
                        <textarea id="response-${requestId}" placeholder="Type your response here..."></textarea>
                        
                        <div class="button-group">
                            <button class="btn-submit" onclick="submitResponse('${requestId}', false)">
                                ✓ Submit Response
                            </button>
                            <button class="btn-error" onclick="submitResponse('${requestId}', true)">
                                ✗ Return Error
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            }
        }
        
        async function submitResponse(requestId, isError) {
            const textarea = document.getElementById(`response-${requestId}`);
            const responseText = textarea.value.trim();
            
            if (!responseText) {
                showNotification('Please enter a response first!');
                return;
            }
            
            try {
                const response = await fetch('/submit_response', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        request_id: requestId,
                        response: responseText,
                        is_error: isError
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(isError ? 'Error response sent!' : 'Response submitted successfully!');
                    completedCount++;
                    updateCounts();
                    fetchRequests();
                } else {
                    showNotification('Failed to submit response');
                }
            } catch (error) {
                console.error('Error submitting response:', error);
                showNotification('Error submitting response');
            }
        }
        
        async function fetchRequests() {
            try {
                const response = await fetch('/get_requests');
                const data = await response.json();
                
                pendingCount = Object.keys(data.requests).length;
                updateCounts();
                renderRequests(data.requests);
            } catch (error) {
                console.error('Error fetching requests:', error);
            }
        }
        
        // Poll for new requests every second
        setInterval(fetchRequests, 1000);
        
        // Initial fetch
        fetchRequests();
    </script>
</body>
</html>
'''

# Flask routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_requests')
def get_requests():
    return jsonify({'requests': pending_requests})

@app.route('/submit_response', methods=['POST'])
def submit_response():
    data = request.json
    request_id = data.get('request_id')
    response_text = data.get('response')
    is_error = data.get('is_error', False)
    
    if request_id in pending_requests:
        completed_responses[request_id] = {
            'response': response_text,
            'is_error': is_error
        }
        del pending_requests[request_id]
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Request not found'})

def run_flask():
    """Run Flask in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# MCP Server
server = Server("human-controlled-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools that the human can respond to"""
    return [
        Tool(
            name="ask_human",
            description="Ask the human operator a question and wait for their response. Use this when you need human input, decision-making, or information that only a human would know.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or request for the human operator"
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context to help the human understand what you need"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="human_search",
            description="Ask the human to search for information. The human will look up the information and provide their findings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What the human should search for"
                    },
                    "sources": {
                        "type": "string",
                        "description": "Suggested sources or where to look (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="human_decision",
            description="Ask the human to make a decision between options. Useful when you need human judgment or preference.",
            inputSchema={
                "type": "object",
                "properties": {
                    "decision_needed": {
                        "type": "string",
                        "description": "What decision needs to be made"
                    },
                    "options": {
                        "type": "string",
                        "description": "The available options (can be a list or description)"
                    },
                    "recommendation": {
                        "type": "string",
                        "description": "Your recommendation (optional)"
                    }
                },
                "required": ["decision_needed", "options"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls by queuing them for human response"""
    
    request_id = str(uuid.uuid4())
    
    # Add to pending requests
    pending_requests[request_id] = {
        'tool_name': name,
        'arguments': arguments,
        'timestamp': datetime.now().isoformat()
    }
    
    logger.info(f"New request queued: {request_id} - {name}")
    
    # Wait for human response (with timeout)
    max_wait = 300  # 5 minutes timeout
    waited = 0
    
    while request_id not in completed_responses and waited < max_wait:
        await asyncio.sleep(1)
        waited += 1
    
    # Get response or timeout
    if request_id in completed_responses:
        response_data = completed_responses[request_id]
        del completed_responses[request_id]
        
        if response_data['is_error']:
            raise Exception(response_data['response'])
        
        return [TextContent(
            type="text",
            text=response_data['response']
        )]
    else:
        # Timeout - clean up
        if request_id in pending_requests:
            del pending_requests[request_id]
        raise Exception("Request timed out - no human response received within 5 minutes")

async def main():
    """Main entry point"""
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("Human MCP Server starting...")
    logger.info("Web interface available at: http://localhost:5000")
    logger.info("Waiting for MCP client connection via stdio...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="human-controlled-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
