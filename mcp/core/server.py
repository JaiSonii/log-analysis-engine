from mcp.server.fastmcp import FastMCP
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AnyMessage
from .state import AgentState
from pydantic import Field
import subprocess
import os
import asyncio

from .builder import build_workflow

from dotenv import load_dotenv
load_dotenv()

async def _run_sandboxed_code(code: str, log_file_path: str) -> str:
    print(f"---Sandbox: Received request to run code.---")
    try:
        host_log_path = os.path.abspath(log_file_path)
        if not os.path.exists(host_log_path):
            return f"Error: Log file not found at {host_log_path}"

        mount_arg = f"{host_log_path}:/app/log.txt:ro" 

        result = await asyncio.to_thread(
            subprocess.run,
            [
                "docker", "run", "--rm", "--network", "none",
                "--memory", "256m", "--cpus", "0.5",
                "-v", mount_arg, "python:3.11-slim",
                "python", "-c", code
            ],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return f"Execution successful. Output:\n{result.stdout}"
        else:
            return f"Execution failed. Error:\n{result.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

mcp = FastMCP(name="Intelligent Python Server", instructions="Intelligently execute natural language python code")

@mcp.tool()
async def delegate_complex_analysis(
    log_list : list[str],
    query : str = Field(description="The natural language analysis task"),
    log_file_path : str = Field(description="The full path to the log file on the host")
):
    """
    Accepts a complex, natural-language analysis task,
    Writes and execute code to answer it and return the final, summarized result
    Args:
        log_list: List of string containing the structure of logs log file
        query : The natural language analysis task
        log_file_path : The full path to the log file on the host
    """

    @tool
    async def execute_code_for_this_query(code : str):
        """
        Executes the given Python code in a sandbox. The log file is at '/app/log.txt' inside the tool.
        The code MUST print its final answer to stdout.
        Args:
            code : The Python code to execute
        Returns:
            The stdout of the executed Python code
        """
        return await _run_sandboxed_code(code=code, log_file_path=log_file_path)

    tools = [execute_code_for_this_query]
    tool_dict = {tool.name : tool for tool in tools}

    chat_model = ChatOpenAI(
        model='gpt-4.1-mini',
        temperature=0
    )
    messages: list[AnyMessage] = [HumanMessage(content=query)]
    agent = await build_workflow(chat_model, tools, tool_dict)
    final_state = await agent.ainvoke(AgentState(messages=messages, max_executions=4, execution_count=0, log_list=log_list))
    return final_state['messages'][-1].content
    
async def test_sandbox():
    code = "print('Hello from inside Docker!')"
    log_path = "C:\\Users\\jaius\\Downloads\\logs\\2025-09-30\\python\\python.log"   # <-- MUST point to an existing file on host
    result = await _run_sandboxed_code(code, log_path)
    print(result)

if __name__ == "__main__":
    print("Starting INTELLIGENT Python Analyzer MCP Server (FastMCP)...")
    print("This server will run forever, waiting for a host to connect.")
    print("Press Ctrl+C to stop.")
    
    mcp.run(transport="stdio")
