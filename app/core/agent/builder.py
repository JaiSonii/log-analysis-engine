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

MAX_EXECUTIONS = 4

async def build_workflow(provider: ModelProvider, tool_maker: ToolMaker, log_list: list[str], log_file_path: str) -> StateGraph:
    """
    Builds the LangGraph-based workflow for the Log Analysis Agent.
    """
    if not log_list:
        raise ValueError("Error - log list was not provided")
    if not log_file_path:
        raise FileExistsError("log_file_path not provided")
    if not provider.model:
        raise ValueError("Model not initialized")

    # Build tools
    tools, tool_dict = await tool_maker()
    print('-----------------------------------------------')
    print(tools)
    print('-----------------------------------------------')
    model_with_tools = provider.model.bind_tools(tools)

    # ----------- LLM NODE -----------
    def llm_node(state: AgentState) -> dict:
        exec_count = state.get("execution_count", 0)
        print(f"[LLM NODE] Execution #{exec_count + 1}")

        # Format the system prompt with dynamic log context
        messages = [
            SystemMessage(LLM_PROMPT.format(log_list=log_list, log_file_path=log_file_path, max_executions=MAX_EXECUTIONS-1, execution_count=exec_count)),
        ] + state["messages"]

        response = model_with_tools.invoke(messages)
        return {
            "messages": [response],
            "execution_count": exec_count + 1,  # increment counter
        }

    # ----------- TOOL NODE -----------
    async def tool_node(state: AgentState) -> dict:
        messages = state["messages"]
        last_message = messages[-1]
        new_tool_messages = []

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")  # This is the (likely faulty) dict from the LLM
                tool_id = tool_call.get("id")

                # --- START FIX: Intercept and correct arguments ---
                if tool_name == "delegate_complex_analysis":
                    print("[Tool Node] Intercepted call to delegate_complex_analysis")
                    
                    # 1. Find the original user query from the message history
                    initial_query = ""
                    for msg in state['messages']:
                        if isinstance(msg, HumanMessage):
                            initial_query = msg.content
                            print(f"[Tool Node] Found user query: {initial_query}")
                            break
                    
                    if not initial_query:
                        # Fallback in case no human message is found (should not happen)
                        initial_query = "Please analyze the logs."

                    # 2. Re-build the tool_args with the *correct* values
                    # We use the log_list and log_file_path from the parent function's scope
                    tool_args = {
                        "query": initial_query,
                        "log_list": log_list,
                        "log_file_path": log_file_path
                    }
                    print(f"[Tool Node] Forcing correct tool arguments.")
                # --- END FIX ---

                if tool_name in tool_dict:
                    try:
                        # 'tool_args' now contains the corrected, valid arguments
                        tool_output = await tool_dict[tool_name].ainvoke(
                            tool_args,
                            config={"configurable": {"tool_call_id": tool_id}},
                        )
                        new_tool_messages.append(
                            ToolMessage(content=str(tool_output), tool_call_id=tool_id)
                        )
                    except Exception as e:
                        new_tool_messages.append(
                            ToolMessage(
                                content=f"Error running tool {tool_name}: {e}",
                                tool_call_id=tool_id,
                            )
                        )
                else:
                    new_tool_messages.append(
                        ToolMessage(
                            content=f"Error: Tool '{tool_name}' not found.",
                            tool_call_id=tool_id,
                        )
                    )
        print(new_tool_messages)
        return {"messages": new_tool_messages}

    # ----------- CONDITIONAL EDGE LOGIC -----------
    def should_continue(state: AgentState) -> Literal["tool_node", "END"]:
        last_message = state["messages"][-1]
        exec_count = state.get("execution_count", 0)

        # Stop if maximum iterations reached
        if exec_count >= MAX_EXECUTIONS:
            print(f"[STOP] Max executions ({MAX_EXECUTIONS}) reached.")
            return "END"

        # Continue if AIMessage includes tool calls
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tool_node"

        return "END"

    # ----------- GRAPH BUILDING -----------
    graph_builder = StateGraph(AgentState, input_schema=AgentInputSchema)

    graph_builder.add_node("llm_node", llm_node)
    graph_builder.add_node("tool_node", tool_node)

    graph_builder.add_edge(START, "llm_node")
    graph_builder.add_conditional_edges(
        "llm_node",
        should_continue,
        {"tool_node": "tool_node", "END": END},
    )
    graph_builder.add_edge("tool_node", "llm_node")

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
