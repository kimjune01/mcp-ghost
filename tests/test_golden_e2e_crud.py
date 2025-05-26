"""
Golden tests for end-to-end CRUD operations using MCP-Ghost with SQLite database.

These tests record real LLM interactions performing database operations through MCP servers.
They demonstrate complete workflows from natural language prompts to database changes.
"""

import asyncio
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from dotenv import load_dotenv

from mcp_ghost.core import mcp_ghost, MCPGhostConfig, MCPGhostResult
from tests.goldens.golden_framework import GoldenRecorder, MockLLMClient

# Load environment variables for testing
load_dotenv()


class TestGoldenE2ECRUD:
    """Golden tests for end-to-end CRUD operations."""
    
    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary SQLite database for testing."""
        import time
        timestamp = int(time.time() * 1000000)  # microsecond timestamp
        with tempfile.NamedTemporaryFile(suffix=f'_golden_{timestamp}.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database with test schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create posts table
        cursor.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield {"path": db_path, "timestamp": timestamp}
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def server_config(self, temp_db):
        """Create MCP server configuration for SQLite."""
        return {
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": ["mcp-server-sqlite", "--db-path", temp_db["path"]]
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_user_golden(self, server_config, temp_db):
        """Test creating a user through MCP-Ghost with golden recording."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
        
        # Create golden recorder
        recorder = GoldenRecorder("test_create_user_e2e", "openai")
        
        # Set input data
        user_prompt = "Create a new user named 'John Doe' with email 'john@example.com' and age 30"
        system_prompt = "You are a helpful database assistant. Use the available SQL tools to help users with database operations. When creating users, use INSERT INTO statements."
        
        recorder.set_input(
            server_config=server_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini",
            namespace="mcp_ghost",
            timeout=30.0,
            max_iterations=5
        )
        
        if recorder.record_mode:
            # Record mode: make actual API call
            config = MCPGhostConfig(
                server_config=server_config,
                system_prompt=system_prompt,
                provider="openai",
                api_key=api_key,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                namespace="mcp_ghost",
                timeout=30.0,
                max_iterations=5
            )
            result = await mcp_ghost(config)
            
            # Since we got back an MCPGhostResult, convert it to dict for golden recording
            result_dict = {
                "success": result.success,
                "final_result": result.final_result,
                "summary": result.summary,
                "tool_chain": [
                    {
                        "iteration": tc.iteration,
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "success": tc.success,
                        "result": tc.result,
                        "error": tc.error,
                        "execution_time": tc.execution_time,
                        "reasoning": tc.reasoning,
                        "retry_attempt": tc.retry_attempt
                    } for tc in result.tool_chain
                ],
                "conversation_history": result.conversation_history,
                "errors": result.errors,
                "execution_metadata": result.execution_metadata
            }
            
            # Record the interaction
            recorder.record_provider_interaction(
                {
                    "messages": [{"role": "user", "content": user_prompt}],
                    "model": "gpt-4o-mini",
                    "tools": []  # Would contain actual MCP tools
                },
                result_dict,
                result.execution_metadata.get("token_usage", {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50})
            )
            
            # Set golden output
            recorder.set_golden_output(result_dict)
            
            # Save the golden file
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            # Replay mode: use mock client
            mock_client = MockLLMClient(recorder)
            result_dict = await mock_client.create_completion(
                messages=[{"role": "user", "content": user_prompt}]
            )
        
        # Verify result structure (works for both modes)
        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "final_result" in result_dict
        assert "tool_chain" in result_dict
        assert "conversation_history" in result_dict
        assert "execution_metadata" in result_dict
    
    @pytest.mark.asyncio
    async def test_schema_discovery_golden(self, server_config, temp_db):
        """Test database schema discovery with golden recording."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
        
        # Create golden recorder
        recorder = GoldenRecorder("test_schema_discovery_e2e", "openai")
        
        user_prompt = "What tables are available in this database and what are their schemas? Please show me the structure of each table."
        system_prompt = "You are a helpful database assistant. Use schema discovery tools to explore database structure and provide clear information about tables and columns."
        
        recorder.set_input(
            server_config=server_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini",
            namespace="mcp_ghost"
        )
        
        if recorder.record_mode:
            config = MCPGhostConfig(
                server_config=server_config,
                system_prompt=system_prompt,
                provider="openai",
                api_key=api_key,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                namespace="mcp_ghost"
            )
            result = await mcp_ghost(config)
            
            # Convert MCPGhostResult to dict
            result_dict = {
                "success": result.success,
                "final_result": result.final_result,
                "summary": result.summary,
                "tool_chain": [
                    {
                        "iteration": tc.iteration,
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "success": tc.success,
                        "result": tc.result,
                        "error": tc.error,
                        "execution_time": tc.execution_time,
                        "reasoning": tc.reasoning,
                        "retry_attempt": tc.retry_attempt
                    } for tc in result.tool_chain
                ],
                "conversation_history": result.conversation_history,
                "errors": result.errors,
                "execution_metadata": result.execution_metadata
            }
            
            recorder.record_provider_interaction(
                {"messages": [{"role": "user", "content": user_prompt}], "model": "gpt-4o-mini"},
                result_dict,
                result.execution_metadata.get("token_usage", {"total_tokens": 160, "prompt_tokens": 100, "completion_tokens": 60})
            )
            
            recorder.set_golden_output(result_dict)
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            mock_client = MockLLMClient(recorder)
            result_dict = await mock_client.create_completion(
                messages=[{"role": "user", "content": user_prompt}]
            )
        
        assert isinstance(result_dict, dict)
        assert "success" in result_dict


class TestGoldenComplexWorkflows:
    """Golden tests for complex multi-step workflows."""
    
    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary SQLite database for testing."""
        import time
        timestamp = int(time.time() * 1000000)  # microsecond timestamp
        with tempfile.NamedTemporaryFile(suffix=f'_golden_complex_{timestamp}.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database with test schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create posts table  
        cursor.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield {"path": db_path, "timestamp": timestamp}
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.fixture
    def server_config(self, temp_db):
        """Create MCP server configuration for SQLite."""
        return {
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": ["mcp-server-sqlite", "--db-path", temp_db["path"]]
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_complete_user_post_workflow_golden(self, server_config, temp_db):
        """Test complete user and post creation workflow with golden recording."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
        
        # Create golden recorder
        recorder = GoldenRecorder("test_complete_user_post_workflow", "openai")
        
        user_prompt = """
        Please help me with a complete blog setup workflow:
        
        1. Create a new user named 'Jane Blogger' with email 'jane@blog.com' and age 28
        2. Create a first post by Jane with title 'Welcome to My Blog' and content 'This is my first blog post where I introduce myself and my passion for writing.'
        3. Create a second post by Jane with title 'My Thoughts on Technology' and content 'Technology has transformed our world in ways we never imagined. Here are my thoughts...'
        4. Show me all posts by Jane with her user information
        5. Update Jane's age to 29 (birthday!)
        6. Show me the updated user profile and confirm the age change
        
        Please explain each step as you complete it and show me the results.
        """
        
        system_prompt = """You are a helpful database assistant specializing in blog management. You can:
        - Create users with INSERT INTO users (name, email, age) VALUES (...)
        - Create posts with INSERT INTO posts (user_id, title, content) VALUES (...)
        - Query data with SELECT statements including JOINs
        - Update records with UPDATE statements
        
        Always explain what you're doing at each step and show the results of your operations."""
        
        recorder.set_input(
            server_config=server_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini",
            namespace="mcp_ghost",
            max_iterations=15,
            enable_backtracking=True,
            conversation_memory=True
        )
        
        if recorder.record_mode:
            config = MCPGhostConfig(
                server_config=server_config,
                system_prompt=system_prompt,
                provider="openai",
                api_key=api_key,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                namespace="mcp_ghost",
                max_iterations=15,
                enable_backtracking=True,
                conversation_memory=True
            )
            result = await mcp_ghost(config)
            
            # Convert to dict for golden recording
            result_dict = {
                "success": result.success,
                "final_result": result.final_result,
                "summary": result.summary,
                "tool_chain": [
                    {
                        "iteration": tc.iteration,
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "success": tc.success,
                        "result": tc.result,
                        "error": tc.error,
                        "execution_time": tc.execution_time,
                        "reasoning": tc.reasoning,
                        "retry_attempt": tc.retry_attempt
                    } for tc in result.tool_chain
                ],
                "conversation_history": result.conversation_history,
                "errors": result.errors,
                "execution_metadata": result.execution_metadata
            }
            
            # Record multiple interactions for multi-step workflow
            recorder.record_provider_interaction(
                {"messages": [{"role": "user", "content": user_prompt}], "model": "gpt-4o-mini"},
                result_dict,
                result.execution_metadata.get("token_usage", {"total_tokens": 650, "prompt_tokens": 350, "completion_tokens": 300})
            )
            
            recorder.set_golden_output(result_dict)
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            mock_client = MockLLMClient(recorder)
            result_dict = await mock_client.create_completion(
                messages=[{"role": "user", "content": user_prompt}]
            )
        
        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        
        # Verify multi-step workflow structure
        if "tool_chain" in result_dict:
            # Should have multiple tool calls for the workflow (at least 6 operations)
            assert len(result_dict["tool_chain"]) >= 6
        
        if "conversation_history" in result_dict:
            # Should have conversation history showing the progression
            assert len(result_dict["conversation_history"]) >= 3
    
    @pytest.mark.asyncio
    async def test_data_analysis_workflow_golden(self, server_config, temp_db):
        """Test data analysis workflow with golden recording."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
        
        # Pre-populate database with sample data
        conn = sqlite3.connect(temp_db["path"])
        cursor = conn.cursor()
        
        # Add sample users
        users_data = [
            ('Alice Johnson', 'alice@email.com', 25),
            ('Bob Smith', 'bob@email.com', 30),
            ('Carol Davis', 'carol@email.com', 22),
            ('David Wilson', 'david@email.com', 35),
            ('Eva Brown', 'eva@email.com', 28)
        ]
        
        for name, email, age in users_data:
            cursor.execute("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", (name, email, age))
        
        # Add sample posts (multiple posts per user)
        posts_data = [
            (1, 'First Post', 'Content of first post'),
            (1, 'Second Post', 'Content of second post'),
            (1, 'Third Post', 'Content of third post'),
            (2, 'Bob\'s Thoughts', 'Bob shares his thoughts'),
            (2, 'More from Bob', 'Another post from Bob'),
            (3, 'Carol\'s Journey', 'Carol talks about her journey'),
            (4, 'David\'s Experience', 'David shares his experience'),
            (4, 'David\'s Update', 'An update from David'),
            (4, 'David\'s Latest', 'David\'s latest thoughts'),
            (5, 'Eva\'s Story', 'Eva tells her story')
        ]
        
        for user_id, title, content in posts_data:
            cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)", (user_id, title, content))
        
        conn.commit()
        conn.close()
        
        # Create golden recorder
        recorder = GoldenRecorder("test_data_analysis_workflow", "openai")
        
        user_prompt = """
        Please help me analyze the blog data in this database:
        
        1. Show me the total number of users and posts
        2. Find the most active user (who has written the most posts)
        3. Show me the average age of all users
        4. List all users who have written more than 2 posts
        5. Show me the 3 most recent posts with their author names
        6. Find users aged between 25 and 30 and show their posts
        
        Please provide clear analysis and insights for each query.
        """
        
        system_prompt = """You are a data analyst assistant. Use SQL queries to analyze blog data and provide insights.
        Use COUNT, AVG, GROUP BY, ORDER BY, and JOIN clauses as needed.
        Always explain your analysis and what the data tells us."""
        
        recorder.set_input(
            server_config=server_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model="gpt-4o-mini",
            namespace="mcp_ghost",
            max_iterations=10
        )
        
        if recorder.record_mode:
            config = MCPGhostConfig(
                server_config=server_config,
                system_prompt=system_prompt,
                provider="openai",
                api_key=api_key,
                user_prompt=user_prompt,
                model="gpt-4o-mini",
                namespace="mcp_ghost",
                max_iterations=10
            )
            result = await mcp_ghost(config)
            
            # Convert to dict
            result_dict = {
                "success": result.success,
                "final_result": result.final_result,
                "summary": result.summary,
                "tool_chain": [
                    {
                        "iteration": tc.iteration,
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments,
                        "success": tc.success,
                        "result": tc.result,
                        "error": tc.error,
                        "execution_time": tc.execution_time,
                        "reasoning": tc.reasoning,
                        "retry_attempt": tc.retry_attempt
                    } for tc in result.tool_chain
                ],
                "conversation_history": result.conversation_history,
                "errors": result.errors,
                "execution_metadata": result.execution_metadata
            }
            
            recorder.record_provider_interaction(
                {"messages": [{"role": "user", "content": user_prompt}], "model": "gpt-4o-mini"},
                result_dict,
                result.execution_metadata.get("token_usage", {"total_tokens": 500, "prompt_tokens": 280, "completion_tokens": 220})
            )
            
            recorder.set_golden_output(result_dict)
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            mock_client = MockLLMClient(recorder)
            result_dict = await mock_client.create_completion(
                messages=[{"role": "user", "content": user_prompt}]
            )
        
        assert isinstance(result_dict, dict)
        assert "success" in result_dict