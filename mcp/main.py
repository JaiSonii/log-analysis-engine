from python_mcp_server import mcp

def main():
    print("Starting INTELLIGENT Python Analyzer MCP Server (FastMCP)...")
    print("This server will run forever, waiting for a host to connect.")
    print("Press Ctrl+C to stop.")
    
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
