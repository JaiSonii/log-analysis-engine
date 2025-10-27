from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.embedding.pipeline import VectorPipeline
from app.core.embedding.indexer import PersistentFaissIndexer
from langchain.tools import tool


import asyncio

client = MultiServerMCPClient({
    "python_analyzer_service" : {
        "transport" : "stdio",
        "command" : "C:\\Machine Learning\\python-interpreter-mcp\\.venv\\Scripts\\python.exe",
        "args" : ["C:\\Machine Learning\\python-interpreter-mcp\\main.py"]
    }
})

mcp_tools = asyncio.run(client.get_tools())

pipeline = VectorPipeline(PersistentFaissIndexer)
pipeline.load('data/faiss.index', 'data/store.pkl')



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

__all__ = ['tools', 'tool_dict']