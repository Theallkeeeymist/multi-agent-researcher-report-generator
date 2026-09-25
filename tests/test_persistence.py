import pytest
import os
from unittest.mock import patch

@pytest.mark.anyio
async def test_postgres_checkpointer_connection():
    """
    Verifies that the PostgreSQL checkpointer environment variables are configured 
    and that the checkpointer can initialize successfully.
    """
    database_url = os.getenv("POSTGRES_DB_URL") or os.getenv("DATABASE_URL")
    
    # If running in an environment without the live DB container, 
    # we verify the configuration structure safely.
    if not database_url:
        pytest.skip("PostgreSQL connection URL not set in environment variables.")

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        
        # Test establishing an async connection pool with the checkpointer
        async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
            # Verify setup creates tables or connects successfully
            await checkpointer.setup()
            assert checkpointer is not None
            
    except ImportError:
        pytest.skip("langgraph-checkpoint-postgres package not installed in the current environment.")
    except Exception as e:
        # If the container is down during local unit testing, catch connection refusals gracefully
        if "Connection refused" in str(e) or "could not translate host name" in str(e):
            pytest.skip("Live PostgreSQL container is not reachable from this test runner context.")
        else:
            raise e