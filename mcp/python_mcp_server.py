from mcp.server.fastmcp import FastMCP
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from pydantic import Field
import subprocess
import os
import asyncio
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
    query : str = Field(description="The natural language analysis task"),
    log_file_path : str = Field(description="The full path to the log file on the host")
):
    """
    Accepts a complex, natural-language analysis task,
    Writes and execute code to answer it and return the final, summarized result
    Args:
        query : The natural language analysis task
        log_file_path : The full path to the log file on the host
    """

    async def execute_code_for_this_query(code : str):
        return _run_sandboxed_code(code=code, log_file_path=log_file_path)

    internal_tool = Tool(
        name="execute_python_code",
        func=execute_code_for_this_query,
        description=(
            "Executes the given Python code in a sandbox. "
            "The log file is at '/app/log.txt'. "
            "The code MUST print its final answer to stdout."
        )
    )

    internal_llm = ChatOpenAI(
        model='gpt-4.1-mini',
        temperature=0
    ).bind_tools([internal_tool])

    system_prompt = (
        "You are an expert Python developer. Your *only* job is to "
        "write and execute code to answer a user's query about a log file. "
        "You must use your 'execute_python_code' tool. "
        "The log file is always at '/app/log.txt' inside the tool. "
        "Do not answer from memory. Always write and run the code."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ]

    try:
        response_1 = await internal_llm.ainvoke(messages)
        messages.append(response_1)

        if not response_1.tool_calls:
            return "ERROR : Agent failed to write the python code"
        
        tool_call = response_1.tool_calls[0]
        code_to_run = tool_call.get('args').get('code')
        exec_result = await execute_code_for_this_query(code_to_run)
        messages.append(ToolMessage(content=exec_result, tool_call_id=tool_call['id']))

        response_2 = await internal_llm.ainvoke(messages)
        return response_2.content
    except Exception as e:
        print(f"Error in execution {e}")
        return f"Error in MCP agent loop: {e}"
    
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
