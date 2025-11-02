from .prompts import SYSTEM_PROMPT
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from typing_extensions import Literal

from .state import AgentState

async def build_workflow(chat_model : ChatOpenAI, tools : list[BaseTool], tool_dict : dict[str, BaseTool])-> CompiledStateGraph:
    model = chat_model.bind_tools(tools)
    async def llm_node(state: AgentState)-> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT.format(log_list=state['log_list'], max_executions=state['max_executions'], execution_count=state['execution_count']))] + state['messages']
        response = await model.ainvoke(messages)
        return {"messages" : [response]}

    async def tool_node(state : AgentState) -> AgentState:
        last_message = state['messages'][-1]
        if isinstance(last_message, AIMessage):
            for tool_call in last_message.tool_calls:
                tool = tool_dict[tool_call['name']]
                tool_result = await tool.ainvoke(tool_call['args'], config={'configurable' : {'tool_call_id' : tool_call['id']}})
                state['messages'].append(ToolMessage(content=tool_result, tool_call_id=tool_call['id']))
                
        return state
    
    def should_continue(state: AgentState)-> Literal['tool_node', 'END']:
        if state['execution_count'] >= state['max_executions']:
            return 'END'
        last_message = state['messages'][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return 'tool_node'
        return 'END'
    
    builder = StateGraph(AgentState)

    builder.add_node('llm_node', llm_node)
    builder.add_node('tool_node', tool_node)

    builder.add_edge(START, 'llm_node')
    builder.add_conditional_edges(
        'llm_node',
        should_continue,
        {
            'tool_node' : 'tool_node',
            'END' : END
        }
    )
    builder.add_edge('tool_node', 'llm_node')

    return builder.compile()