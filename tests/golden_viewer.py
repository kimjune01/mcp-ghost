#!/usr/bin/env python3
"""
Golden Test Viewer - Web interface for inspecting MCP-Ghost golden test files.

Usage:
    python golden_viewer.py [--port 8080] [--host localhost]

Opens a web interface to browse and inspect golden test files with:
- Interactive golden file browser
- Formatted JSON viewer
- Conversation flow visualization
- Performance metrics dashboard
- Provider comparison tools
"""

import argparse
import json
import os
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import html


class GoldenViewerHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving golden test viewer."""
    
    def __init__(self, *args, **kwargs):
        self.goldens_dir = Path(__file__).parent / "goldens"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/" or parsed_url.path == "/index.html":
            self.serve_index()
        elif parsed_url.path == "/api/goldens":
            self.serve_golden_list()
        elif parsed_url.path.startswith("/api/golden/"):
            self.serve_golden_file(parsed_url.path[12:])  # Remove /api/golden/
        elif parsed_url.path == "/api/providers":
            self.serve_provider_stats()
        else:
            super().do_GET()
    
    def serve_index(self):
        """Serve the main HTML interface."""
        html_content = self.generate_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(html_content.encode()))
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_golden_list(self):
        """Serve list of all golden files."""
        goldens = []
        
        for provider_dir in self.goldens_dir.iterdir():
            if provider_dir.is_dir() and provider_dir.name != "__pycache__":
                provider = provider_dir.name
                for golden_file in provider_dir.glob("*.json"):
                    try:
                        with open(golden_file) as f:
                            data = json.load(f)
                        
                        goldens.append({
                            "provider": provider,
                            "test_name": data.get("test_name", golden_file.stem),
                            "file_path": f"{provider}/{golden_file.name}",
                            "recorded_at": data.get("recorded_at"),
                            "user_prompt": data.get("input", {}).get("user_prompt", "")[:100],
                            "success": data.get("golden_output", {}).get("success", None),
                            "iterations": len(data.get("provider_responses", [])),
                            "tokens": data.get("golden_output", {}).get("execution_metadata", {}).get("token_usage", {}).get("total_tokens", 0)
                        })
                    except (json.JSONDecodeError, IOError) as e:
                        print(f"Error reading {golden_file}: {e}")
        
        # Sort by provider, then by test name
        goldens.sort(key=lambda x: (x["provider"], x["test_name"]))
        
        self.send_json_response(goldens)
    
    def serve_golden_file(self, file_path):
        """Serve a specific golden file."""
        try:
            golden_path = self.goldens_dir / file_path
            if not golden_path.exists():
                self.send_error(404, f"Golden file not found: {file_path}")
                return
            
            with open(golden_path) as f:
                data = json.load(f)
            
            self.send_json_response(data)
        except (json.JSONDecodeError, IOError) as e:
            self.send_error(500, f"Error reading golden file: {e}")
    
    def serve_provider_stats(self):
        """Serve provider statistics."""
        stats = {}
        
        for provider_dir in self.goldens_dir.iterdir():
            if provider_dir.is_dir() and provider_dir.name != "__pycache__":
                provider = provider_dir.name
                golden_files = list(provider_dir.glob("*.json"))
                
                total_tokens = 0
                total_tests = len(golden_files)
                successful_tests = 0
                
                for golden_file in golden_files:
                    try:
                        with open(golden_file) as f:
                            data = json.load(f)
                        
                        if data.get("golden_output", {}).get("success"):
                            successful_tests += 1
                        
                        tokens = data.get("golden_output", {}).get("execution_metadata", {}).get("token_usage", {}).get("total_tokens", 0)
                        total_tokens += tokens
                    except (json.JSONDecodeError, IOError):
                        pass
                
                stats[provider] = {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                    "total_tokens": total_tokens,
                    "avg_tokens": (total_tokens / total_tests) if total_tests > 0 else 0
                }
        
        self.send_json_response(stats)
    
    def send_json_response(self, data):
        """Send JSON response."""
        json_data = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', len(json_data.encode()))
        self.end_headers()
        self.wfile.write(json_data.encode())
    
    def generate_html(self):
        """Generate the main HTML interface."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP-Ghost Golden Test Viewer</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header h1 { margin: 0; color: #333; }
        .header p { margin: 5px 0 0 0; color: #666; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { margin: 0 0 10px 0; color: #333; font-size: 14px; text-transform: uppercase; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2563eb; }
        .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
        .main-content { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }
        .sidebar { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: fit-content; }
        .content { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .golden-list { list-style: none; padding: 0; margin: 0; }
        .golden-item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.2s; }
        .golden-item:hover { background: #f8fafc; }
        .golden-item.selected { background: #e0f2fe; border-left: 3px solid #2563eb; }
        .golden-item .name { font-weight: bold; color: #333; }
        .golden-item .provider { color: #666; font-size: 12px; }
        .golden-item .prompt { color: #888; font-size: 11px; margin-top: 2px; }
        .json-viewer { font-family: 'Courier New', monospace; background: #f8f9fa; padding: 15px; border-radius: 4px; overflow: auto; max-height: 600px; }
        .conversation-flow { margin-top: 20px; }
        .message { padding: 10px; margin: 5px 0; border-radius: 8px; }
        .message.user { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .message.assistant { background: #f3e5f5; border-left: 4px solid #9c27b0; }
        .message.tool { background: #e8f5e8; border-left: 4px solid #4caf50; }
        .message-role { font-weight: bold; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }
        .message-content { white-space: pre-wrap; }
        .tool-calls { margin-top: 10px; }
        .tool-call { background: #fff3e0; padding: 8px; border-radius: 4px; margin: 5px 0; font-size: 12px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .metric { background: #f8f9fa; padding: 10px; border-radius: 4px; text-align: center; }
        .metric-value { font-size: 20px; font-weight: bold; color: #2563eb; }
        .metric-label { font-size: 12px; color: #666; margin-top: 5px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .tabs { display: flex; border-bottom: 2px solid #eee; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border-bottom: 2px solid transparent; }
        .tab.active { border-bottom-color: #2563eb; color: #2563eb; font-weight: bold; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .provider-badge { background: #2563eb; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 5px; }
        .success-badge { background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
        .failure-badge { background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 MCP-Ghost Golden Test Viewer</h1>
            <p>Interactive browser for inspecting golden test files and provider performance</p>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <div class="loading">Loading provider statistics...</div>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <h3>Golden Test Files</h3>
                <ul class="golden-list" id="goldenList">
                    <li class="loading">Loading golden files...</li>
                </ul>
            </div>
            
            <div class="content">
                <div id="goldenDetails">
                    <div class="loading">Select a golden test file from the sidebar to view details</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentGoldenData = null;
        
        // Load provider statistics
        async function loadProviderStats() {
            try {
                const response = await fetch('/api/providers');
                const stats = await response.json();
                
                const statsGrid = document.getElementById('statsGrid');
                statsGrid.innerHTML = '';
                
                Object.entries(stats).forEach(([provider, data]) => {
                    const card = document.createElement('div');
                    card.className = 'stat-card';
                    card.innerHTML = `
                        <h3>${provider.toUpperCase()}</h3>
                        <div class="stat-value">${data.total_tests}</div>
                        <div class="stat-label">Total Tests</div>
                        <div style="margin-top: 10px;">
                            <div style="font-size: 14px; color: #10b981;">${data.success_rate.toFixed(1)}% Success</div>
                            <div style="font-size: 12px; color: #666;">${data.total_tokens.toLocaleString()} tokens used</div>
                        </div>
                    `;
                    statsGrid.appendChild(card);
                });
            } catch (error) {
                console.error('Error loading provider stats:', error);
            }
        }
        
        // Load golden file list
        async function loadGoldenList() {
            try {
                const response = await fetch('/api/goldens');
                const goldens = await response.json();
                
                const goldenList = document.getElementById('goldenList');
                goldenList.innerHTML = '';
                
                goldens.forEach((golden, index) => {
                    const item = document.createElement('li');
                    item.className = 'golden-item';
                    item.dataset.filePath = golden.file_path;
                    
                    const successBadge = golden.success === true ? 
                        '<span class="success-badge">✓</span>' : 
                        golden.success === false ? '<span class="failure-badge">✗</span>' : '';
                    
                    item.innerHTML = `
                        <div class="name">${golden.test_name} ${successBadge}</div>
                        <div class="provider">
                            ${golden.provider}<span class="provider-badge">${golden.iterations} calls</span>
                            ${golden.tokens > 0 ? `<span style="font-size: 10px; color: #666; margin-left: 5px;">${golden.tokens} tokens</span>` : ''}
                        </div>
                        <div class="prompt">${golden.user_prompt}${golden.user_prompt.length >= 100 ? '...' : ''}</div>
                    `;
                    
                    item.addEventListener('click', () => loadGoldenDetails(golden.file_path, item));
                    goldenList.appendChild(item);
                });
            } catch (error) {
                console.error('Error loading golden list:', error);
                document.getElementById('goldenList').innerHTML = '<li class="error">Error loading golden files</li>';
            }
        }
        
        // Load golden file details
        async function loadGoldenDetails(filePath, item) {
            try {
                // Update selection
                document.querySelectorAll('.golden-item').forEach(el => el.classList.remove('selected'));
                item.classList.add('selected');
                
                const response = await fetch(`/api/golden/${filePath}`);
                currentGoldenData = await response.json();
                
                displayGoldenDetails(currentGoldenData);
            } catch (error) {
                console.error('Error loading golden details:', error);
                document.getElementById('goldenDetails').innerHTML = '<div class="error">Error loading golden file details</div>';
            }
        }
        
        // Display golden file details
        function displayGoldenDetails(data) {
            const detailsContainer = document.getElementById('goldenDetails');
            
            const tabs = `
                <div class="tabs">
                    <div class="tab active" onclick="showTab('overview')">Overview</div>
                    <div class="tab" onclick="showTab('conversation')">Conversation</div>
                    <div class="tab" onclick="showTab('metrics')">Metrics</div>
                    <div class="tab" onclick="showTab('raw')">Raw JSON</div>
                </div>
            `;
            
            const overviewTab = createOverviewTab(data);
            const conversationTab = createConversationTab(data);
            const metricsTab = createMetricsTab(data);
            const rawTab = `<div class="tab-content" id="raw"><pre class="json-viewer">${JSON.stringify(data, null, 2)}</pre></div>`;
            
            detailsContainer.innerHTML = tabs + overviewTab + conversationTab + metricsTab + rawTab;
        }
        
        function createOverviewTab(data) {
            const input = data.input || {};
            const output = data.golden_output || {};
            
            return `
                <div class="tab-content active" id="overview">
                    <h3>Test: ${data.test_name}</h3>
                    <p><strong>Provider:</strong> ${input.provider}</p>
                    <p><strong>Model:</strong> ${input.model || 'Default'}</p>
                    <p><strong>Recorded:</strong> ${data.recorded_at ? new Date(data.recorded_at).toLocaleString() : 'Unknown'}</p>
                    
                    <h4>Input</h4>
                    <div class="message user">
                        <div class="message-role">User Prompt</div>
                        <div class="message-content">${input.user_prompt || 'No prompt'}</div>
                    </div>
                    
                    <div class="message assistant">
                        <div class="message-role">System Prompt</div>
                        <div class="message-content">${(input.system_prompt || 'No system prompt').substring(0, 200)}${(input.system_prompt || '').length > 200 ? '...' : ''}</div>
                    </div>
                    
                    <h4>Result</h4>
                    <p><strong>Success:</strong> ${output.success ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Summary:</strong> ${output.summary || 'No summary'}</p>
                    ${output.final_result ? `<p><strong>Response:</strong> ${(output.final_result.response || 'No response').substring(0, 300)}${(output.final_result.response || '').length > 300 ? '...' : ''}</p>` : ''}
                </div>
            `;
        }
        
        function createConversationTab(data) {
            const history = data.golden_output?.conversation_history || [];
            
            let conversationHtml = '<div class="tab-content" id="conversation"><h3>Conversation Flow</h3>';
            
            if (history.length === 0) {
                conversationHtml += '<p>No conversation history available</p>';
            } else {
                history.forEach((message, index) => {
                    const content = message.content || '[No content]';
                    const toolCalls = message.tool_calls || [];
                    
                    conversationHtml += `
                        <div class="message ${message.role}">
                            <div class="message-role">${message.role}</div>
                            <div class="message-content">${content}</div>
                            ${toolCalls.length > 0 ? `
                                <div class="tool-calls">
                                    <strong>Tool Calls (${toolCalls.length}):</strong>
                                    ${toolCalls.map(call => `
                                        <div class="tool-call">
                                            <strong>${call.function?.name || 'Unknown'}</strong>: ${call.function?.arguments || '{}'}
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                });
            }
            
            conversationHtml += '</div>';
            return conversationHtml;
        }
        
        function createMetricsTab(data) {
            const metadata = data.golden_output?.execution_metadata || {};
            const providerResponses = data.provider_responses || [];
            
            return `
                <div class="tab-content" id="metrics">
                    <h3>Performance Metrics</h3>
                    
                    <div class="metrics-grid">
                        <div class="metric">
                            <div class="metric-value">${metadata.total_execution_time || 'N/A'}</div>
                            <div class="metric-label">Execution Time (s)</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${metadata.total_iterations || providerResponses.length}</div>
                            <div class="metric-label">Total Iterations</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${metadata.success_rate || 'N/A'}</div>
                            <div class="metric-label">Success Rate (%)</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${metadata.token_usage?.total_tokens || 'N/A'}</div>
                            <div class="metric-label">Total Tokens</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${metadata.token_usage?.prompt_tokens || 'N/A'}</div>
                            <div class="metric-label">Prompt Tokens</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${metadata.token_usage?.completion_tokens || 'N/A'}</div>
                            <div class="metric-label">Completion Tokens</div>
                        </div>
                    </div>
                    
                    <h4>Provider Interactions</h4>
                    ${providerResponses.map((response, index) => `
                        <div style="background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 4px;">
                            <strong>Iteration ${response.iteration}</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                                Tokens: ${response.token_usage?.total_tokens || 'N/A'} 
                                (${response.token_usage?.prompt_tokens || 0} prompt + ${response.token_usage?.completion_tokens || 0} completion)
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        function showTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
        }
        
        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            loadProviderStats();
            loadGoldenList();
        });
    </script>
</body>
</html>'''


def main():
    """Main function to start the golden viewer server."""
    parser = argparse.ArgumentParser(description='MCP-Ghost Golden Test Viewer')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve on (default: 8080)')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t automatically open browser')
    
    args = parser.parse_args()
    
    # Change to the tests directory to serve static files
    os.chdir(Path(__file__).parent)
    
    server = HTTPServer((args.host, args.port), GoldenViewerHandler)
    
    url = f"http://{args.host}:{args.port}"
    print(f"🚀 Starting MCP-Ghost Golden Test Viewer")
    print(f"📂 Serving golden tests from: {Path(__file__).parent / 'goldens'}")
    print(f"🌐 Server running at: {url}")
    print(f"⏹️  Press Ctrl+C to stop")
    
    # Start server in a separate thread so we can open browser after it's ready
    import threading
    import time
    
    def start_server():
        server.serve_forever()
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give server a moment to start up
    time.sleep(0.5)
    
    if not args.no_browser:
        print(f"🔍 Opening browser...")
        webbrowser.open(url)
    
    try:
        # Keep main thread alive
        while server_thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\n👋 Shutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()