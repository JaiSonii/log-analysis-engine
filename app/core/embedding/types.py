from typing_extensions import Optional, TypedDict
from datetime import datetime

class Log(TypedDict):
    timestamp : Optional[datetime]
    is_error : bool
    message : str
    level : Optional[str]

class ChunkMetaData(TypedDict):
    start_timestamp : Optional[datetime]
    end_timestamp : Optional[datetime]
    has_error : bool

class Chunk(TypedDict):
    text : str
    metadata : ChunkMetaData