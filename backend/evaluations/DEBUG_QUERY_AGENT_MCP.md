# Query Agent MCP Integration - Debug Analysis

**Date**: December 18, 2025  
**Issue**: query_agent writes perfect SQL but doesn't execute queries via MCP tools

## Current Setup Analysis

### 1. MCP Server Initialization (Production vs Evaluation)

**Production Setup** ([query_tools.py](../src/ai/tools/query_tools.py)):
```python
# Module-level singleton
_mcp_server: MCPServerStdio | None = None

async def initialize_mcp_server() -> None:
    """Called during FastAPI lifespan startup"""
    global _mcp_server
    
    if _mcp_server is not None:
        return  # Already initialized
    
    database_uri = _get_database_uri()  # Gets from config.DATABASE_URL
    _mcp_server = MCPServerStdio(
        name="Postgres MCP",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres", database_uri, "--access-mode=restricted"],
        },
    )
    
    await _mcp_server.__aenter__()  # Start subprocess
    
    # Add MCP server to query_agent
    from src.ai.app_agents.query_agent import query_agent
    query_agent.mcp_servers = [_mcp_server]
```

**Evaluation Setup** ([agent_runners.py](agent_runners.py)):
```python
async def run_query_agent(**inputs) -> dict[str, Any]:
    """Run query_agent with MLflow dataset inputs."""
    from src.ai.tools.query_tools import initialize_mcp_server, cleanup_mcp_server
    
    try:
        # Initialize MCP server for database access
        await initialize_mcp_server()  # ← Calls production function
        
        # Run query agent
        result = await Runner.run(
            starting_agent=query_agent,
            input=agent_input,
            session=None
        )
        
        return {"response": result.final_output, ...}
    finally:
        await cleanup_mcp_server()  # ← Closes MCP server after EACH test case
```

### 2. Database Credentials

**Production DATABASE_URL** (from `.env`):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/fitness_bot
```

**MCP Server Conversion** ([query_tools.py#L31](../src/ai/tools/query_tools.py#L31)):
```python
def _get_database_uri() -> str:
    """Convert asyncpg format to standard postgresql for postgres-mcp"""
    database_url = settings.DATABASE_URL
    
    # Convert: postgresql+asyncpg://... → postgresql://...
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Convert hostname 'db' to 'localhost' for MCP server
    database_url = database_url.replace("@db:", "@localhost:")
    
    return database_url
```

**Result**: `postgresql://postgres:postgres@localhost:5432/fitness_bot`

### 3. Test Data Availability

**Current Status**:
```sql
SELECT id, status FROM fitness_plans WHERE user_id = 'c2608a59-3af8-4600-9de3-3ce004d40187'
-- Result: []  (NO DATA)
```

**Expected Test User**: `eval_test_user@fitness.ai` (UUID: `c2608a59-3af8-4600-9de3-3ce004d40187`)

**Problem**: Test user exists but has **NO fitness plan data** to query!

### 4. Root Cause Analysis

**Why query_agent doesn't execute MCP tools:**

1. ✅ **MCP Server Initialized**: `initialize_mcp_server()` is called
2. ✅ **MCP Server Added to Agent**: `query_agent.mcp_servers = [_mcp_server]`
3. ✅ **Database Credentials**: Properly converted for postgres-mcp
4. ⚠️ **Cleanup After Each Test**: `cleanup_mcp_server()` called in finally block
5. ❌ **NO TEST DATA**: eval_test_user has no fitness plans to query!

**Hypothesis**: Agent may be:
- Not calling MCP tools (prompt issue)
- MCP tools failing silently due to no data
- Database connection not working in evaluation context

## Key Questions

### Q1: Should we use separate PostgreSQL instance for evaluations?

**Option A: Same DB (Current Approach)**
- ✅ Simpler setup
- ✅ Uses real production schema
- ✅ Can test against production-like data
- ❌ Risk of polluting dev data
- ❌ Tests depend on external state

**Option B: Separate Test DB**
- ✅ Clean isolation
- ✅ Can reset easily between test runs
- ✅ Parallel test execution safe
- ✅ No risk to dev data
- ❌ More complex setup (docker-compose, migrations)
- ❌ Need to maintain separate data fixtures

**Recommendation for Portfolio Project**: 
- **Start with Option A** (same DB, simpler)
- **Migrate to Option B** if tests become flaky or data management becomes complex
- Use read-only queries (no mutations) to minimize pollution risk

### Q2: How should we create test data?

**Option A: Manual Setup Script** (Current)
- Script: `setup_test_user.py`
- Create once, use for all tests
- Risk: Data gets stale or inconsistent

**Option B: Pytest Fixtures**
- Create/teardown data per test run
- Always fresh data
- More complex, slower

**Option C: Database Fixtures**
- SQL dump of test data
- Load at startup
- Fast, consistent

**Recommendation**: 
- **Start with Option A** (manual script)
- Ensure script creates **COMPLETE** fitness plan (not just user)
- Re-run script before each evaluation session

### Q3: What's actually blocking query_agent execution?

**Next Debug Steps**:

1. **Verify MCP Server Connection**:
   ```python
   # Add logging to run_query_agent
   print(f"MCP Server: {_mcp_server}")
   print(f"Query Agent MCP Servers: {query_agent.mcp_servers}")
   print(f"MCP Server Connected: {_mcp_server is not None}")
   ```

2. **Test Manual Query Execution**:
   ```python
   # Outside evaluation framework
   await initialize_mcp_server()
   result = await Runner.run(query_agent, "List all tables in the database")
   print(result.final_output)
   ```

3. **Check Agent Prompt**:
   - Does query_agent know to USE the MCP tools?
   - Current instructions say "use the postgres-mcp MCP tools" but maybe not explicit enough?

4. **Check Tool Availability at Runtime**:
   ```python
   # In run_query_agent, after initialize_mcp_server()
   if query_agent.mcp_servers:
       tools = await query_agent.mcp_servers[0].list_tools()
       print(f"Available MCP tools: {tools}")
   ```

## Immediate Action Items

### Priority 1: Create Complete Test Data (HIGH)
**Problem**: eval_test_user has no fitness plan to query  
**Fix**: Update `setup_test_user.py` to create complete fitness plan

```python
# backend/evaluations/setup_test_user.py
async def create_complete_test_user():
    # 1. Create user
    # 2. Create fitness_plan with status='active'
    # 3. Create phases
    # 4. Create workout_plan with details
    # 5. Create workouts and exercises
    # 6. Create meal_plan with daily_calorie_target
    # 7. Create meals with meal_details
    
    print(f"✓ Created complete test user with queryable data")
```

### Priority 2: Add MCP Server Debugging (MEDIUM) - **VALIDATED CORRECT APPROACH** ✅
**Problem**: Can't see if MCP server is working  
**Fix**: Add logging to `agent_runners.py`

**OpenAI Agents SDK MCP Documentation Confirms**:
- MCPServerStdio is the CORRECT transport for postgres-mcp
- Agent.mcp_servers list should contain the server instance
- Server is added at runtime: `query_agent.mcp_servers = [_mcp_server]` ✅
- Use async context manager: `await _mcp_server.__aenter__()` ✅

**postgres-mcp Documentation Confirms**:
- Command format: `npx -y @modelcontextprotocol/server-postgres <DATABASE_URI> --access-mode=restricted` ✅
- Database URI format: `postgresql://user:pass@host:port/dbname` ✅
- Automatic hostname remapping: localhost → host.docker.internal (Mac/Windows) ✅
- Tools provided: execute_sql, list_schemas, list_objects, get_object_details, explain_query, etc.

**Current Implementation Status: CORRECT** ✅
Our implementation matches the documented best practices:
```python
_mcp_server = MCPServerStdio(
    name="Postgres MCP",
    params={
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", database_uri, "--access-mode=restricted"],
    },
)
await _mcp_server.__aenter__()  # Initialize subprocess
query_agent.mcp_servers = [_mcp_server]  # Add to agent
```

**Debugging to Add**:
```python
async def run_query_agent(**inputs):
    try:
        await initialize_mcp_server()
        
        # DEBUG: Verify MCP server connection
        from src.ai.tools.query_tools import _mcp_server
        from src.ai.app_agents.query_agent import query_agent
        
        print(f"[DEBUG] MCP Server initialized: {_mcp_server is not None}")
        print(f"[DEBUG] Query agent has MCP servers: {len(query_agent.mcp_servers) if query_agent.mcp_servers else 0}")
        
        if query_agent.mcp_servers:
            try:
                tools = await query_agent.mcp_servers[0].list_tools()
                print(f"[DEBUG] Available MCP tools: {[t.name for t in tools]}")
            except Exception as e:
                print(f"[DEBUG] Failed to list MCP tools: {e}")
        
        # Run agent...
```

### Priority 3: Verify Database Connection (MEDIUM)
**Problem**: MCP server may not be connecting to database  
**Fix**: Test manual query before evaluation

```bash
# Test postgres-mcp directly
cd backend
npx -y @modelcontextprotocol/server-postgres \
  postgresql://postgres:postgres@localhost:5432/fitness_bot \
  --access-mode=restricted
```

### Priority 4: Update Query Agent Prompt (LOW)
**Problem**: Agent may not know to USE MCP tools explicitly  
**Fix**: Make tool usage more explicit in instructions

```python
instructions = """...

CRITICAL WORKFLOW:
1. When you receive a query request, ALWAYS use the execute_sql MCP tool
2. Generate the SQL query based on the schema above
3. Call execute_sql with your SQL query
4. Format and return the results

Example:
User: "Get my fitness plan"
→ You MUST call execute_sql("SELECT * FROM fitness_plans WHERE user_id = '...' AND status = 'active'")
→ Format and return the results

DO NOT just describe the SQL - EXECUTE IT using the execute_sql tool.
"""
```

## Expected Workflow After Fixes

1. **Database Running**: `docker-compose up -d db`
2. **Test Data Created**: `uv run python evaluations/setup_test_user.py`
3. **Verify Data**: Query via MCP to confirm fitness plan exists
4. **Run Evaluation**: `uv run python evaluations/run_evaluation.py --agent query_agent`
5. **Agent Executes**:
   - MCP server initializes
   - query_agent receives query request
   - Agent calls `execute_sql` MCP tool
   - MCP server executes query
   - Agent returns real data
6. **Judge Evaluates**: "excellent" - SQL correct AND executed

## Database Setup Decision

**For this portfolio project, I recommend:**

### Phase 1 (Now): Same Database, Manual Setup
- Use existing dev database
- Create comprehensive test data script
- Run script before evaluation sessions
- Simple, fast to implement

### Phase 2 (Later, if needed): Separate Test Database
- Create `docker-compose.test.yml`
- Separate database: `fitness_bot_test`
- Automated fixtures via pytest
- Safer for parallel testing

**Rationale**: 
- Portfolio project focuses on demonstrating best practices, not production scale
- Same DB is simpler and gets us testing faster (fail-fast philosophy)
- Can show understanding of trade-offs in documentation
- Easy to migrate later if complexity grows

## Next Steps

1. **Fix test data** (setup_test_user.py - create complete fitness plan)
2. **Add debugging** (agent_runners.py - log MCP connection status)
3. **Verify database** (ensure Docker container running)
4. **Re-run evaluation** with debugging enabled
5. **Document findings** in RESULTS.md

---

**Status**: Ready to fix - clear path forward  
**Blocking**: NO (can fix independently)  
**Complexity**: Medium (2-3 hours including testing)
