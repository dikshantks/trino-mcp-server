# Contributing to Trino MCP Server

Thank you for your interest in contributing to Trino MCP Server! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd trino-mcp-server
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export TRINO_HOST="localhost"
   export TRINO_PORT="8088"
   export TRINO_USER="trino"
   export TRINO_CATALOG="tpch"
   export TRINO_SCHEMA="tiny"
   ```

4. **Run the server locally**:
   ```bash
   python trino_server.py
   ```

5. **Test changes**:
   ```bash
   echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python trino_server.py
   ```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function parameters and return types
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)

### Docstrings

- Use Google-style docstrings
- Include description, parameters, return type, and examples
- Example:
  ```python
  def example_function(param: str) -> str:
      """
      Brief description of the function.
      
      Args:
          param: Description of the parameter
      
      Returns:
          Description of the return value
      
      Example:
          >>> example_function("test")
          "result"
      """
  ```

### Type Hints

- Always include type hints for function signatures
- Use `typing` module for complex types
- Example:
  ```python
  from typing import Optional, List, Dict
  
  def process_data(items: List[str], config: Optional[Dict[str, str]] = None) -> str:
      ...
  ```

## Adding New Features

### Adding a New Tool

1. **Create the function**:
   ```python
   @mcp.tool()
   async def new_tool(param: str = "") -> str:
       """
       Description of what the tool does.
       
       Args:
           param: Description of parameter
       
       Returns:
           Formatted result string
       """
       # Implementation
   ```

2. **Follow security guidelines**:
   - If executing queries, use `validate_query()` to ensure read-only
   - Never allow write operations
   - Limit result sizes appropriately

3. **Add error handling**:
   - Use `format_error_message()` for user-friendly errors
   - Log errors appropriately
   - Provide helpful troubleshooting hints

4. **Test thoroughly**:
   - Test with valid inputs
   - Test with invalid inputs
   - Test error conditions
   - Test edge cases

### Security Considerations

- **Never allow write operations**: All queries must be read-only
- **Validate all inputs**: Check parameters before using them
- **Limit result sizes**: Prevent overwhelming responses
- **Sanitize error messages**: Don't expose sensitive information
- **Use secure defaults**: Default to secure configurations

## Testing

### Manual Testing

1. **Test locally**:
   ```bash
   python trino_server.py
   ```

2. **Test with Docker**:
   ```bash
   docker build -t trino-mcp-server:latest .
   docker run -i --rm -e TRINO_HOST=host.docker.internal trino-mcp-server:latest
   ```

3. **Test in Cursor**:
   - Build Docker image
   - Configure Cursor MCP
   - Test each tool through Cursor

### Test Checklist

- [ ] All tools work correctly
- [ ] Error handling works properly
- [ ] Read-only enforcement works
- [ ] Authentication works (if applicable)
- [ ] Docker build succeeds
- [ ] Cursor integration works

## Documentation

### Updating Documentation

- Update `README.md` for user-facing changes
- Update `CHANGELOG.md` for all changes
- Add examples for new features
- Update troubleshooting section if needed

### Documentation Style

- Use clear, concise language
- Include code examples
- Provide platform-specific instructions when needed
- Keep examples simple and focused

## Pull Request Process

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following style guidelines
   - Add tests if applicable
   - Update documentation

3. **Commit your changes**:
   ```bash
   git commit -m "Add: Description of changes"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**:
   - Provide clear description of changes
   - Reference any related issues
   - Include testing instructions

### Commit Message Format

- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Prefix with type: `Add:`, `Fix:`, `Update:`, `Remove:`

Examples:
- `Add: Support for HTTPS connections`
- `Fix: Connection error handling on Linux`
- `Update: Documentation for authentication setup`

## Reporting Issues

### Bug Reports

Include:
- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Docker version, Cursor version)
- Relevant logs or error messages

### Feature Requests

Include:
- Description of the feature
- Use case or motivation
- Proposed implementation (if applicable)
- Examples of how it would be used

## Questions?

- Check existing documentation
- Review existing issues
- Open a new issue for discussion

Thank you for contributing! 🚀
