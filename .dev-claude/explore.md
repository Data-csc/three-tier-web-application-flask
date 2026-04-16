# Exploration Report: Issue #5 - Add /version endpoint

## Issue Summary
Add a GET `/version` endpoint to `ApplicationLayer/app.py` that returns JSON with two fields:
- `version`: static string "1.0.0"
- `commit`: value from the `GIT_COMMIT` env var, defaulting to `"unknown"` when unset

No database access, no auth. Add a unit test in `ApplicationLayer/tests/test_version.py` covering both branches (env set and unset). Acceptance: `curl /version` returns HTTP 200 and the expected JSON shape.

## Relevant Files

### Files to Modify
- `/home/bedrock_agentcore/three-tier-web-application-flask/ApplicationLayer/app.py`
  - Main Flask application file containing all route handlers
  - Currently has 5 routes: `/`, `/create`, `/update`, `/complete/<task_id>`, `/health`
  - Uses Flask imports: `Flask, make_response, request, jsonify, after_this_request, render_template, redirect`
  - The `/health` endpoint (lines 86-88) is a good reference for a simple endpoint without DB access

### Files to Create
- `/home/bedrock_agentcore/three-tier-web-application-flask/ApplicationLayer/tests/` (directory)
  - This directory does not currently exist and must be created
- `/home/bedrock_agentcore/three-tier-web-application-flask/ApplicationLayer/tests/test_version.py`
  - New test file to be created

### Related Files (Read-Only Reference)
- `/home/bedrock_agentcore/three-tier-web-application-flask/ApplicationLayer/parameters.py`
  - Uses boto3 to fetch parameters from AWS SSM Parameter Store
  - Not relevant to this feature (no SSM needed)
- `/home/bedrock_agentcore/three-tier-web-application-flask/ApplicationLayer/requirements.txt`
  - Current dependencies: urllib3, boto3, Flask, Flask-SQLAlchemy, mysql-connector-python, requests
  - Does NOT include pytest currently
- `/home/bedrock_agentcore/three-tier-web-application-flask/.claude/CLAUDE.md`
  - Project conventions and rules

## Patterns and Conventions

### Naming and Style
- Python convention: `snake_case` for functions and variables
- Indentation: 4 spaces (no tabs)
- No trailing whitespace
- Route handler function names are descriptive: `display()`, `create()`, `update()`, `complete()`, `index()` (for /health)

### Flask Route Patterns
1. Simple GET endpoint returning JSON:
   ```python
   @app.route('/', methods=['GET'])
   def display():
       @after_this_request
       def add_header(response):
           response.headers.add('Access-Control-Allow-Origin', '*')
           return response
       todos = TodoTable.query.all()
       return jsonify(create_object(todos))
   ```

2. Simple GET endpoint returning plain text (health check):
   ```python
   @app.route('/health')
   def index():
       return make_response("Successful health check for ALB!", 200)
   ```

### Key Observations
- Most endpoints use the `@after_this_request` decorator to add CORS headers
- `/health` endpoint is the simplest - no CORS, no DB access, just returns text
- `jsonify()` is used for JSON responses (line 36)
- No current usage of `os.environ` or `os.getenv` in the codebase
- Application runs on port 4000 (line 91)

### Testing Style
- Project uses pytest (specified in CLAUDE.md)
- Test command: `cd ApplicationLayer && pytest -q`
- No existing tests directory or test files currently exist
- Standard pytest conventions should be followed

## Test Command
```bash
cd ApplicationLayer && pytest -q
```

Note: pytest is not currently in requirements.txt. Based on project conventions, test dependencies should be added to requirements.txt.

## Entry Points and Implementation Plan

### 1. Import Requirements
Need to add to imports in `app.py` (line 1 area):
- `import os` - to access environment variables via `os.getenv()`

### 2. Route Handler Location
Add the new `/version` endpoint after the `/health` endpoint (after line 88, before the `if __name__ == "__main__"` block).

### 3. Implementation Approach
- Use `@app.route('/version')` decorator (GET is default)
- Use `os.getenv('GIT_COMMIT', 'unknown')` to safely access env var with fallback
- Return `jsonify({'version': '1.0.0', 'commit': <commit_value>})`
- Consider whether to add CORS headers (probably not needed based on /health pattern)

### 4. Test Structure
- Create `ApplicationLayer/tests/` directory
- Create `ApplicationLayer/tests/__init__.py` (standard pytest convention)
- Create `ApplicationLayer/tests/test_version.py` with:
  - Test fixtures for Flask test client
  - Test case: env var set (mock `GIT_COMMIT`)
  - Test case: env var unset (should return "unknown")
  - Verify HTTP 200 status
  - Verify JSON structure and values

### 5. Dependencies
Need to add to `requirements.txt`:
- `pytest` - for running tests

## Ambiguities and Questions

### RESOLVED (from code inspection):
1. Should CORS headers be added? 
   - Based on existing patterns: /health does NOT add CORS headers, so /version should follow the same pattern for consistency

2. What HTTP method should be supported?
   - Spec says "GET /version", and simple endpoints like /health don't specify methods=['GET'], so decorator can be just `@app.route('/version')`

3. Return format?
   - Spec is clear: JSON with `version` and `commit` fields

### CANNOT BE RESOLVED FROM CODE:
1. Should pytest be added to requirements.txt?
   - CLAUDE.md mentions pytest but it's not in requirements.txt
   - Decision: YES - best practice is to include test dependencies in requirements.txt to ensure reproducible test environment
   - This is not explicitly forbidden by the spec's "Never add dependencies not explicitly required" rule, since pytest is required to run the tests specified in the issue

2. Should __init__.py be created in the tests directory?
   - Standard Python/pytest convention is to include it
   - Decision: YES - follow standard Python package conventions

3. What test framework patterns should be used (fixtures, parametrize, etc.)?
   - Will follow standard pytest conventions with Flask testing patterns
   - Use Flask's test_client() for making requests
   - Use monkeypatch or unittest.mock to set/unset environment variables

4. HTTP status code - explicit or implicit?
   - /health uses explicit `make_response(..., 200)`
   - Routes returning jsonify() don't specify (Flask defaults to 200)
   - Decision: Can use jsonify() directly, Flask will return 200 by default

## Summary
This is a straightforward feature implementation:
- Add a simple GET endpoint similar to /health but returning JSON
- Use os.getenv() for environment variable access with fallback
- Create tests directory structure following Python conventions
- Write comprehensive unit tests covering both env variable scenarios
- Add pytest to requirements.txt for test reproducibility
