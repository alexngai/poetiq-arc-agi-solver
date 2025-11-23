"""
Tool definitions for computer use agents.
"""

from typing import List, Dict, Any, Optional
import os
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ToolDefinition:
    """Definition of a tool that can be used by the agent."""

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
    ):
        """
        Initialize a tool definition.

        Args:
            name: Name of the tool
            description: Description of what the tool does
            input_schema: JSON schema for the tool's input parameters
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_anthropic_tool(self) -> Dict[str, Any]:
        """
        Convert to Anthropic tool format.

        Returns:
            Tool definition in Anthropic format
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolExecutor:
    """Executes tools for computer use agents."""

    def __init__(self, allowed_paths: Optional[List[str]] = None):
        """
        Initialize tool executor.

        Args:
            allowed_paths: List of allowed paths for file operations
        """
        self.allowed_paths = allowed_paths or []

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            String result from the tool execution
        """
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input.get("path", ""))

            elif tool_name == "list_directory":
                return self._list_directory(
                    tool_input.get("path", "."),
                    tool_input.get("recursive", False),
                )

            elif tool_name == "search_files":
                return self._search_files(
                    tool_input.get("pattern", ""),
                    tool_input.get("path", "."),
                )

            elif tool_name == "search_code":
                return self._search_code(
                    tool_input.get("pattern", ""),
                    tool_input.get("path", "."),
                    tool_input.get("file_pattern", None),
                )

            elif tool_name == "run_command":
                return self._run_command(
                    tool_input.get("command", ""),
                    tool_input.get("cwd", None),
                )

            else:
                return f"Error: Unknown tool '{tool_name}'"

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def _check_path_allowed(self, path: str) -> bool:
        """Check if a path is in the allowed paths."""
        if not self.allowed_paths:
            return True  # No restrictions

        abs_path = os.path.abspath(path)
        for allowed in self.allowed_paths:
            allowed_abs = os.path.abspath(allowed)
            if abs_path.startswith(allowed_abs):
                return True

        return False

    def _read_file(self, path: str) -> str:
        """Read a file and return its contents."""
        if not self._check_path_allowed(path):
            return f"Error: Access denied to path: {path}"

        try:
            file_path = Path(path)

            if not file_path.exists():
                return f"Error: File not found: {path}"

            if not file_path.is_file():
                return f"Error: Not a file: {path}"

            # Read file with size limit
            max_size = 100000  # 100KB
            if file_path.stat().st_size > max_size:
                return f"Error: File too large (max {max_size} bytes): {path}"

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return f"File: {path}\n\n{content}"

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _list_directory(self, path: str, recursive: bool = False) -> str:
        """List contents of a directory."""
        if not self._check_path_allowed(path):
            return f"Error: Access denied to path: {path}"

        try:
            dir_path = Path(path)

            if not dir_path.exists():
                return f"Error: Directory not found: {path}"

            if not dir_path.is_dir():
                return f"Error: Not a directory: {path}"

            files = []
            dirs = []

            if recursive:
                for item in dir_path.rglob("*"):
                    rel_path = item.relative_to(dir_path)
                    if item.is_file():
                        files.append(str(rel_path))
                    elif item.is_dir():
                        dirs.append(str(rel_path))
            else:
                for item in dir_path.iterdir():
                    if item.is_file():
                        files.append(item.name)
                    elif item.is_dir():
                        dirs.append(item.name)

            result = f"Directory: {path}\n\n"

            if dirs:
                result += "Directories:\n"
                for d in sorted(dirs)[:100]:  # Limit output
                    result += f"  {d}/\n"
                if len(dirs) > 100:
                    result += f"  ... and {len(dirs) - 100} more\n"

            if files:
                result += "\nFiles:\n"
                for f in sorted(files)[:100]:  # Limit output
                    result += f"  {f}\n"
                if len(files) > 100:
                    result += f"  ... and {len(files) - 100} more\n"

            return result

        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def _search_files(self, pattern: str, path: str = ".") -> str:
        """Search for files matching a pattern."""
        if not self._check_path_allowed(path):
            return f"Error: Access denied to path: {path}"

        try:
            dir_path = Path(path)

            if not dir_path.exists():
                return f"Error: Directory not found: {path}"

            matches = list(dir_path.rglob(pattern))[:50]  # Limit to 50 results

            if not matches:
                return f"No files found matching pattern: {pattern}"

            result = f"Files matching '{pattern}':\n\n"
            for match in matches:
                result += f"  {match}\n"

            if len(matches) == 50:
                result += "\n  ... (limited to 50 results)"

            return result

        except Exception as e:
            return f"Error searching files: {str(e)}"

    def _search_code(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: Optional[str] = None,
    ) -> str:
        """Search for code pattern in files using grep."""
        if not self._check_path_allowed(path):
            return f"Error: Access denied to path: {path}"

        try:
            # Build grep command
            cmd = ["grep", "-r", "-n", "-i", pattern, path]

            if file_pattern:
                cmd.extend(["--include", file_pattern])

            # Limit results
            cmd.append("--max-count=20")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout
                if len(output) > 5000:
                    output = output[:5000] + "\n... (truncated)"
                return f"Search results for '{pattern}':\n\n{output}"
            elif result.returncode == 1:
                return f"No matches found for pattern: {pattern}"
            else:
                return f"Error searching code: {result.stderr}"

        except subprocess.TimeoutExpired:
            return "Error: Search timed out"
        except Exception as e:
            return f"Error searching code: {str(e)}"

    def _run_command(self, command: str, cwd: Optional[str] = None) -> str:
        """
        Run a safe command (read-only operations only).

        Args:
            command: Command to run
            cwd: Working directory

        Returns:
            Command output
        """
        # Whitelist of safe commands
        safe_commands = [
            "ls", "cat", "head", "tail", "grep", "find", "tree",
            "git log", "git show", "git diff", "git status",
        ]

        # Check if command starts with a safe prefix
        is_safe = any(command.startswith(safe) for safe in safe_commands)

        if not is_safe:
            return f"Error: Command not allowed for security reasons: {command}"

        if cwd and not self._check_path_allowed(cwd):
            return f"Error: Access denied to path: {cwd}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=cwd,
            )

            output = result.stdout
            if result.stderr:
                output += f"\n\nSTDERR:\n{result.stderr}"

            if len(output) > 5000:
                output = output[:5000] + "\n... (truncated)"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error running command: {str(e)}"


# Define available tools
AVAILABLE_TOOLS = [
    ToolDefinition(
        name="read_file",
        description="Read the contents of a file. Use this to read documentation, code files, or any text file.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (relative or absolute)",
                }
            },
            "required": ["path"],
        },
    ),
    ToolDefinition(
        name="list_directory",
        description="List contents of a directory. Use this to explore the structure of documentation or code repositories.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the directory to list",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively (default: false)",
                },
            },
            "required": ["path"],
        },
    ),
    ToolDefinition(
        name="search_files",
        description="Search for files matching a glob pattern. Use this to find specific files by name.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.md', '**/*.py')",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                },
            },
            "required": ["pattern"],
        },
    ),
    ToolDefinition(
        name="search_code",
        description="Search for a pattern in code files using grep. Use this to find specific code, functions, or documentation text.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for (regex supported)",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional file pattern to filter (e.g., '*.py', '*.md')",
                },
            },
            "required": ["pattern"],
        },
    ),
    ToolDefinition(
        name="run_command",
        description="Run a safe read-only command (ls, cat, grep, git log, etc.). Use this to gather information about the repository.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to run (only safe read-only commands allowed)",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command",
                },
            },
            "required": ["command"],
        },
    ),
]


def get_tools() -> List[ToolDefinition]:
    """Get list of available tools."""
    return AVAILABLE_TOOLS
