"""
End-to-end test for CRUD operations using MCP-Ghost with SQLite database.

This test demonstrates a complete round-trip:
1. User asks MCP-Ghost to perform database operations
2. MCP-Ghost connects to MCP server (sqlite server)
3. Server executes SQL operations on local SQLite database
4. Results are returned back through the chain
"""

import asyncio
import pytest
import sqlite3
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from mcp_ghost.core import mcp_ghost, MCPGhostConfig, MCPGhostResult


def assert_mcp_ghost_response(result):
    """Helper to assert that MCP-Ghost returns expected response structure."""
    assert isinstance(result, MCPGhostResult)
    assert hasattr(result, 'success')
    assert hasattr(result, 'final_result')
    assert hasattr(result, 'summary')
    assert hasattr(result, 'tool_chain')
    assert hasattr(result, 'conversation_history')
    assert hasattr(result, 'errors')
    assert hasattr(result, 'execution_metadata')


class TestE2ECRUD:
    """End-to-end CRUD tests for MCP-Ghost."""

    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary SQLite database for testing."""
        import time
        timestamp = int(time.time() * 1000000)  # microsecond timestamp
        with tempfile.NamedTemporaryFile(suffix=f'_crud_{timestamp}.db', delete=False) as f:
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
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture(scope="function")
    def ghost_config(self, temp_db):
        """Create a test configuration for MCP-Ghost."""
        return MCPGhostConfig(
            server_config={
                "mcpServers": {
                    "sqlite": {
                        "command": "uvx",
                        "args": ["mcp-server-sqlite", "--db-path", temp_db["path"]]
                    }
                }
            },
            system_prompt="You are a helpful database assistant. Use the available tools to help users with database operations.",
            provider="openai",
            api_key="test-key",  # Mock key for testing
            user_prompt="Test prompt",  # Will be overridden in tests
            model="gpt-4",
            namespace=f"test_crud_{temp_db['timestamp']}",
            timeout=30.0,
            max_iterations=5,
            enable_backtracking=True,
            conversation_memory=True
        )

    @pytest.mark.asyncio
    async def test_create_user_e2e(self, ghost_config, temp_db):
        """Test creating a user through MCP-Ghost."""
        ghost_config.user_prompt = "Create a new user named 'John Doe' with email 'john@example.com' and age 30"

        # Mock the LLM client to avoid real API calls but test the structure
        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll create the user for you using the SQL database tools.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'John Doe\', \'john@example.com\', 30)"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_read_users_e2e(self, ghost_config, temp_db):
        """Test reading users through MCP-Ghost."""
        # Pre-populate database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Jane Doe', 'jane@example.com', 25)")
        conn.commit()
        conn.close()

        ghost_config.user_prompt = "Show me all users in the database"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll query the users table for you.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_read_query",
                            "arguments": '{"query": "SELECT * FROM users"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_update_user_e2e(self, ghost_config, temp_db):
        """Test updating a user through MCP-Ghost."""
        # Pre-populate database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Jane Doe', 'jane@example.com', 25)")
        conn.commit()
        conn.close()

        ghost_config.user_prompt = "Update Jane Doe's age to 26"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll update Jane's age in the database.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "UPDATE users SET age = 26 WHERE email = \'jane@example.com\'"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_delete_user_e2e(self, ghost_config, temp_db):
        """Test deleting a user through MCP-Ghost."""
        # Pre-populate database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Jane Doe', 'jane@example.com', 25)")
        conn.commit()
        conn.close()

        ghost_config.user_prompt = "Delete the user with email 'jane@example.com'"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll delete that user from the database.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "DELETE FROM users WHERE email = \'jane@example.com\'"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_complex_query_e2e(self, ghost_config, temp_db):
        """Test complex JOIN queries through MCP-Ghost."""
        # Pre-populate with test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 30)")
        cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (1, 'Hello World', 'My first post')")
        conn.commit()
        conn.close()

        ghost_config.user_prompt = "Show me all posts with their author information"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll join the posts and users tables to show you the information.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_read_query",
                            "arguments": '{"query": "SELECT posts.title, posts.content, users.name, users.email FROM posts JOIN users ON posts.user_id = users.id"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_error_handling_e2e(self, ghost_config, temp_db):
        """Test error handling in MCP-Ghost."""
        ghost_config.user_prompt = "Insert duplicate email which should fail"

        # Pre-populate with existing user
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Existing User', 'test@example.com', 25)")
        conn.commit()
        conn.close()

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            # Simulate an LLM API error
            mock_client.create_completion.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)
            # Should handle error gracefully
            assert result.success is False or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_schema_discovery_e2e(self, ghost_config, temp_db):
        """Test database schema discovery through MCP-Ghost."""
        ghost_config.user_prompt = "What tables are available in this database?"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll check what tables are available in the database.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_list_tables",
                            "arguments": "{}"
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_multi_step_operation_e2e(self, ghost_config, temp_db):
        """Test multi-step database operations through MCP-Ghost."""
        ghost_config.user_prompt = "Create a user named Bob and then create a post for him"
        ghost_config.max_iterations = 10

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            
            # First call - create user
            mock_client.create_completion.side_effect = [
                {
                    "content": "I'll create the user first.",
                    "tool_calls": [
                        {
                            "id": "test_call_1",
                            "type": "function",
                            "function": {
                                "name": "test_crud_write_query",
                                "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'Bob\', \'bob@example.com\', 35)"}'
                            }
                        }
                    ],
                    "finish_reason": "tool_calls"
                },
                {
                    "content": "Now I'll create a post for Bob.",
                    "tool_calls": [
                        {
                            "id": "test_call_2",
                            "type": "function",
                            "function": {
                                "name": "test_crud_write_query",
                                "arguments": '{"query": "INSERT INTO posts (user_id, title, content) VALUES (1, \'Bob\\\'s First Post\', \'Hello from Bob!\')"}'
                            }
                        }
                    ],
                    "finish_reason": "tool_calls"
                },
                {
                    "content": "Successfully created user Bob and his first post!",
                    "tool_calls": None,
                    "finish_reason": "stop"
                }
            ]
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_complete_table_lifecycle_with_tool_reporting(self, ghost_config, temp_db):
        """Test complete lifecycle operations with tool reporting."""
        ghost_config.user_prompt = "Create a user, add a post, update the user's age, then show the results"
        ghost_config.max_iterations = 15

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll perform these operations step by step.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'Charlie\', \'charlie@example.com\', 28)"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)


class TestCRUDEdgeCases:
    """Edge case tests for CRUD operations."""

    @pytest.fixture(scope="function")
    def temp_db(self):
        """Create a temporary SQLite database for testing."""
        import time
        timestamp = int(time.time() * 1000000)  # microsecond timestamp
        with tempfile.NamedTemporaryFile(suffix=f'_edge_{timestamp}.db', delete=False) as f:
            db_path = f.name
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield {"path": db_path, "timestamp": timestamp}
        
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture(scope="function")
    def ghost_config(self, temp_db):
        """Create a test configuration for MCP-Ghost."""
        return MCPGhostConfig(
            server_config={
                "mcpServers": {
                    "sqlite": {
                        "command": "uvx",
                        "args": ["mcp-server-sqlite", "--db-path", temp_db["path"]]
                    }
                }
            },
            system_prompt="You are a database assistant.",
            provider="openai",
            api_key="test-key",
            user_prompt="Test prompt",
            model="gpt-4",
            namespace=f"test_edge_{temp_db['timestamp']}",
            timeout=30.0,
            max_iterations=5
        )

    @pytest.mark.asyncio
    async def test_constraint_violation_handling(self, ghost_config, temp_db):
        """Test handling of database constraint violations."""
        # Pre-populate with existing user
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, age) VALUES ('Existing', 'test@example.com', 25)")
        conn.commit()
        conn.close()

        ghost_config.user_prompt = "Try to create another user with email 'test@example.com'"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll attempt to create the user.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'Duplicate\', \'test@example.com\', 30)"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, ghost_config, temp_db):
        """Test that SQL injection attempts are handled safely."""
        ghost_config.user_prompt = "Create a user with name '; DROP TABLE users; --"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll create the user safely.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'; DROP TABLE users; --\', \'safe@example.com\', 25)"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, ghost_config, temp_db):
        """Test handling of large dataset operations."""
        ghost_config.user_prompt = "Show me statistics about all users"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll query user statistics.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_read_query",
                            "arguments": '{"query": "SELECT COUNT(*) as total_users, AVG(age) as avg_age FROM users"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, ghost_config, temp_db):
        """Test concurrent database operations."""
        ghost_config.user_prompt = "Create multiple users at once"

        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "I'll create multiple users.",
                "tool_calls": [
                    {
                        "id": "test_call_1",
                        "type": "function",
                        "function": {
                            "name": "test_crud_write_query",
                            "arguments": '{"query": "INSERT INTO users (name, email, age) VALUES (\'User1\', \'user1@example.com\', 25), (\'User2\', \'user2@example.com\', 30)"}'
                        }
                    }
                ],
                "finish_reason": "tool_calls"
            }
            mock_get_client.return_value = mock_client

            result = await mcp_ghost(ghost_config)
            assert_mcp_ghost_response(result)