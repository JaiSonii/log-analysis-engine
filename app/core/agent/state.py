from langgraph.graph import MessagesState
from typing_extensions import List, Optional

class AgentState(MessagesState):
    log_list : List[str]
    logging_config : Optional[str]
    repomix_context : str
    log_start : Optional[str]
    