from langgraph.graph import MessagesState
from typing_extensions import List, Optional, TypedDict

class AgentState(MessagesState):
    log_list : List[str]
    log_file_path : str
    logging_config : Optional[str]
    repomix_context : str
    log_start : Optional[str]
    total_calls : int
    execution_count : int

class AgentInputSchema(MessagesState):
    log_list : List[str]
    log_file_path : str
    