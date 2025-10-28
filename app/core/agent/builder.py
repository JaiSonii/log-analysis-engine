from .state import AgentState, AgentInputSchema
from .tools import ToolMaker
from .prompts import LLM_PROMPT
from .model_provider import ModelProvider

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph,  START, END

from langgraph.types import Command
from typing_extensions import Literal

from dotenv import load_dotenv
load_dotenv()

def build_workflow(provider :ModelProvider, tool_maker : ToolMaker, log_list : list[str], log_file_path : str)-> StateGraph:
    """
    main method to build the agent workflow
    Args:
        Instance of ModelProvider Class
    Returns:
        Agent Workflow for log analysis
    """
    if not log_list:
        raise ValueError('Error - log list was not provided')
    if not log_file_path:
        raise FileExistsError('log_file_path not provided')
    if not provider.model:
        raise ValueError('Model not initialized')
    tools, tool_dict = tool_maker()
    model_with_tools = provider.model.bind_tools(tools)

    def llm_node(state: AgentState) -> dict:
        messages = [SystemMessage(LLM_PROMPT.format(log_list, log_file_path))] + state['messages']
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

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

    def shoud_continue(state : AgentState) -> Literal['tool_node','END']:
        """
        Checks the last message in the state to decide the next step.
        """
        last_message = state['messages'][-1]
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return 'tool_node'
        
        return 'END'
    
    graph_builder = StateGraph(AgentState, input_schema=AgentInputSchema)

    graph_builder.add_node('llm_node', llm_node)
    graph_builder.add_node('tool_node', tool_node)

    graph_builder.add_edge(START,'llm_node')
    graph_builder.add_conditional_edges(
        'llm_node',
        shoud_continue,
        {
            'tool_node' :'tool_node',
            'END' : END
        }
    )
    graph_builder.add_edge('tool_node','llm_node')

    return graph_builder



# async def main():
#     graph = graph_builder.compile()
#     import sys
    
#     repomix_path = 'C:\\web development projects\\FOG\\laser-tag\\fog-laser-tag\\src\\moments\\repomix-output.xml'
#     logging_path = 'data\\python.log'
    
#     repomix_context = ""
#     try:
#         with open(repomix_path, 'r', encoding='utf-8') as f: # <-- CHANGED
#             repomix_context = f.read()
#     except FileNotFoundError:
#         print(f"Error: repomix_path not found at {repomix_path}")
#         sys.exit(1)
#     except Exception as e:
#         print(f"Error reading repomix_path: {e}")
#         sys.exit(1)
    
#     print(f"Loaded {len(repomix_context)} characters from repomix_context.")

#     log_list = log_flow_node(repomix_context=repomix_context)
    
    
#     state = AgentInputSchema(
#         messages=[
#             SystemMessage(LLM_PROMPT.format(log_list=log_list, log_file_path=logging_path)),
#             HumanMessage(content="How Mant camera errors are there?")
#         ],
#         log_list=log_list,
#         log_file_path=logging_path
#     )

#     print("\n--- Invoking Async Graph ---")
#     final_state = await graph.ainvoke(state)
#     print("--- Graph Execution Complete ---")
    
#     for message in final_state['messages']:
#         print(f"{'-'*20} {message.type} {'-'*20}")
#         print(message.content)


# if __name__ == '__main__':
#     from dotenv import load_dotenv
#     import asyncio
#     load_dotenv()

#     asyncio.run(main())
