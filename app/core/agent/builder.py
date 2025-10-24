from .state import AgentState
from .helpers import extract_logs_from_repomix
from langgraph.graph import StateGraph,  START, END
from langgraph.types import Command
from typing_extensions import Literal

# First lets build the demo workflow

def log_flow_node(state: AgentState):
    """
    Local function to extract log statements from the repomix_context
    using XML parsing and RegEx.
    """
    print("Extracting logs using local function...")
    try:
        repomix_context = state.get('repomix_context')
        
        if not repomix_context:
            print("Error: repomix_context is empty. Cannot analyze logs.")
            return state
        
        # Call the new helper function to do the work (use configured start token or default)
        start_str = state.get('log_start') or 'logger'
        log_list = extract_logs_from_repomix(repomix_context, start_str)
        
        
        # Update the state with the results
        state['log_list'] = log_list
        return state

    except Exception as e:
        print(f"An error occurred during log extraction: {e}")
        return state
    
def llm_node(state : AgentState) -> AgentState:
    return state

def tool_node(state : AgentState):
    return state

def summary_node(state: AgentState):
    return state

def shoud_continue(state : AgentState) -> Literal['tool_node','summary_node']:
    bulbul = True
    if bulbul:
        return 'tool_node'
    else:
        return 'summary_node'
    
graph_builder = StateGraph(AgentState)
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






if __name__ == '__main__':
    graph = graph_builder.compile()
    print(graph.get_graph().draw_mermaid())
    # import sys
    # repomix_path = 'C:\\web development projects\\FOG\\laser-tag\\fog-laser-tag\\src\\moments\\repomix-output.xml'
    # logging_path = 'C:\\web development projects\\FOG\\laser-tag\\fog-laser-tag\\src\\moments\\app\\core\\logger.py'
    
    # repomix_context = ""
    # try:
    #     with open(repomix_path, 'r', encoding='utf8') as f:
    #         repomix_context = f.read()
    # except FileNotFoundError:
    #     print(f"Error: repomix_path not found at {repomix_path}")
    #     sys.exit(1) # Use sys.exit
    # except Exception as e:
    #     print(f"Error reading repomix_path: {e}")
    #     sys.exit(1)

    # logging_config = ""
    # try:
    #     with open(logging_path, 'r') as f:
    #         logging_config = f.read()
    # except FileNotFoundError:
    #     print(f"Error: logging_path not found at {logging_path}")
    #     # This might not be critical if the local function doesn't use it
    #     # But for consistency with your original code, we'll exit
    #     sys.exit(1)
    # except Exception as e:
    #     print(f"Error reading logging_path: {e}")
    #     sys.exit(1)
    
    # # Assuming AgentState is a dict-like object as implied by .get()
    # state: AgentState = {
    #     'messages': [], 
    #     'log_list': [], 
    #     'logging_config': logging_config, 
    #     'repomix_context': repomix_context, 
    #     'log_start': None
    # }
    
    # print(f"Loaded {len(repomix_context)} characters from repomix_context.")
    # print(f"Loaded {len(logging_config)} characters from logging_config.")

    # updated_state = log_flow_node(state)
    
    # print("\n--- Final Log Flow ---")
    # if updated_state.get('log_flow'):
    #     for log in updated_state['log_list']:
    #         print(f"- {log}")
    # else:
    #     print("No log flow was generated.")