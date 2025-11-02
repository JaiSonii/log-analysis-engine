from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.embedding.pipeline import VectorPipeline
from app.core.embedding.indexer import PersistentFaissIndexer, InMemoryIndexer
from langchain.tools import tool
import os

from typing_extensions import Optional

class ToolMaker:
    def __init__(self, db_type : str, log_file_path : Optional[str] = None, faiss_path : Optional[str] = None, store_path : Optional[str] = None) -> None:
        self._db_type = db_type
        self.pipe = self._init_pipeline(log_file_path=log_file_path, faiss_path=faiss_path, store_path=store_path)
        self.mcp_client = MultiServerMCPClient({
                "python_analyzer_service" : {
                    "transport" : "stdio",
                    "command" : "C:\\Machine Learning\\log-analyzer\\mcp\\.venv\\Scripts\\python.exe",
                    "args" : ["C:\\Machine Learning\\log-analyzer\\mcp\\main.py"]
                }
            })
    
    async def __call__(self):
        """
        Retrieves One query tool and one mcp tool
        Returns:
            A tuple containing list of tools and tool_dict
        """
        query_tool = self._get_vector_tool()
        mcp_tools = await self._get_mcp_tools()

        tools = [query_tool] + mcp_tools
        tool_dict = {tool.name : tool for tool in tools}
        return tools, tool_dict
        
    async def _get_mcp_tools(self):
        return await self.mcp_client.get_tools()
    
    def _get_vector_tool(self):
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
            return self.pipe.query(text, k)
        return query_tool

    def _init_pipeline(self, **kwargs):
        pipe : Optional[VectorPipeline]= None
        if self._db_type == 'memory':
            log_file_path = kwargs.get('log_file_path',None)
            if not log_file_path  or not os.path.exists(log_file_path):
                raise FileExistsError('log_file_path does not exists')
            pipe = VectorPipeline(InMemoryIndexer)
            pipe.create_db(log_file_path)
        else:
            log_file_path = kwargs.get('log_file_path')
            faiss_path = kwargs.get('faiss_path')
            store_path = kwargs.get('store_path')
            if not faiss_path:
                raise ValueError('Provide faiss_path for persistent indexer')
            if not store_path:
                raise ValueError('Provide store_path for persistent indexer')

            pipe = VectorPipeline(PersistentFaissIndexer)
            if log_file_path:
                pipe.create_db(log_file_path)
            pipe.load(faiss_path, store_path)
        return pipe
