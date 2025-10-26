from .state import AgentState, AgentInputSchema
from .helpers import extract_logs_from_repomix
from langgraph.graph import StateGraph,  START, END
from langgraph.types import Command
from typing_extensions import Literal
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.core.embedding.pipeline import VectorPipeline
from app.core.embedding.indexer import PersistentFaissIndexer
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain.tools import tool
from .prompts import LLM_PROMPT

from langchain_mcp_adapters.client import MultiServerMCPClient

import asyncio
from dotenv import load_dotenv
import os
load_dotenv()

pipeline = VectorPipeline(PersistentFaissIndexer)
pipeline.load('data/faiss.index', 'data/store.pkl')

client = MultiServerMCPClient({
    "python_analyzer_service" : {
        "transport" : "stdio",
        "command" : "C:\\Machine Learning\\python-interpreter-mcp\\.venv\\Scripts\\python.exe",
        "args" : ["C:\\Machine Learning\\python-interpreter-mcp\\main.py"]
    }
})

mcp_tools = asyncio.run(client.get_tools())

@tool
def query_tool(text : str, k : int = 3):
    """
        Query the the vector Database
        Args:
            text : the query text to perform search
            k : number of documents to retrieve (default - 3)
        Returns:
            A list of similar documents
    """
    return pipeline.query(text, k)

tools = [query_tool] + mcp_tools
tool_dict = {tool.name : tool for tool in tools}

# First lets build the demo workflow

model = ChatOpenAI(
    model='gpt-4.1-mini',
    temperature = 0.3,
    api_key = lambda: os.getenv('OPENAI_API_KEY', '')
)

model_with_tools = model.bind_tools(tools)

def log_flow_node(repomix_context : str, log_start : str | None = None):
    """
    Local function to extract log statements from the repomix_context
    using XML parsing and RegEx.
    """
    log_list = []
    print("Extracting logs using local function...")
    try:
        
        if not repomix_context:
            print("Error: repomix_context is empty. Cannot analyze logs.")
            return []
        
        # Call the new helper function to do the work (use configured start token or default)
        start_str = log_start or 'logger'
        log_list = extract_logs_from_repomix(repomix_context, start_str)
        
        return log_list

    except Exception as e:
        print(f"An error occurred during log extraction: {e}")
        return []
    
# NEW (Correct)
def llm_node(state: AgentState) -> dict:
    messages = state['messages']
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

# NEW (Correct)
async def tool_node(state: AgentState) -> dict:
    messages = state['messages']
    last_message = messages[-1]
    
    new_tool_messages = []
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args')
            tool_id = tool_call.get('id')  

            if tool_name in tool_dict:
                try:
                    tool_output = await tool_dict[tool_name].ainvoke(tool_args, config={'configurable' : {'tool_call_id' : tool_id}})
                    new_tool_messages.append(ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_id  # <-- Pass the id here
                    ))
                except Exception as e:
                    new_tool_messages.append(ToolMessage(
                        content=f"Error running tool {tool_name}: {e}",
                        tool_call_id=tool_id
                    ))
            else:
                 new_tool_messages.append(ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.",
                    tool_call_id=tool_id
                ))
                
    return {"messages": new_tool_messages} 

def summary_node(state: AgentState):
    return state

def shoud_continue(state : AgentState) -> Literal['tool_node','summary_node']:
    """
    Checks the last message in the state to decide the next step.
    """
    last_message = state['messages'][-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return 'tool_node'
    
    return 'summary_node'
    
graph_builder = StateGraph(AgentState, input_schema=AgentInputSchema)
graph_builder.add_node('llm_node', llm_node)
graph_builder.add_node('tool_node', tool_node)
graph_builder.add_node('summary_node', summary_node)

graph_builder.add_edge(START, 'llm_node')
graph_builder.add_conditional_edges(
    'llm_node',
    shoud_continue,
    {
        'tool_node' : 'tool_node',
        'summary_node' : 'summary_node'
    }
)

graph_builder.add_edge('tool_node', 'llm_node')
graph_builder.add_edge('summary_node', END)



async def main():
    graph = graph_builder.compile()
    import sys
    
    repomix_path = 'C:\\web development projects\\FOG\\laser-tag\\fog-laser-tag\\src\\moments\\repomix-output.xml'
    logging_path = 'data\\python.log'
    
    repomix_context = ""
    try:
        with open(repomix_path, 'r', encoding='utf-8') as f: # <-- CHANGED
            repomix_context = f.read()
    except FileNotFoundError:
        print(f"Error: repomix_path not found at {repomix_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading repomix_path: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(repomix_context)} characters from repomix_context.")

    log_list = log_flow_node(repomix_context=repomix_context)
    
    
    state = AgentInputSchema(
        messages=[
            SystemMessage(LLM_PROMPT.format(log_list=log_list, log_file_path=logging_path)),
            HumanMessage(content="How Mant camera errors are there?")
        ],
        log_list=log_list,
        log_file_path=logging_path
    )

    print("\n--- Invoking Async Graph ---")
    final_state = await graph.ainvoke(state)
    print("--- Graph Execution Complete ---")
    
    for message in final_state['messages']:
        print(f"{'-'*20} {message.type} {'-'*20}")
        print(message.content)


if __name__ == '__main__':
    from dotenv import load_dotenv
    import asyncio
    load_dotenv()

    asyncio.run(main())
