from langgraph.graph import MessagesState
from typing_extensions import TypedDict
class AgentState(MessagesState):
    max_executions : int
    execution_count : int
    log_list : list[str]

class AgentInputSchema(TypedDict):
    max_executions : int
    execution_count : int