from swiggy.client import MCPClient, unwrap_tool_result

def main():
    print("=" * 70)
    print("LOOTDEAL - SWIGGY MCP DIAGNOSTIC")
    print("=" * 70)

    mcp = MCPClient()

    try:
        print("Initializing...")
        result = mcp.initialize()
        print("Initialize OK.")

        try:
            mcp.initialized()
        except Exception:
            pass

        tools = unwrap_tool_result(mcp.list_tools())
        print("\nTools/list response received.")

        names = []
        if isinstance(tools, dict):
            result_obj = tools.get("result", tools)
            tool_list = result_obj.get("tools", []) if isinstance(result_obj, dict) else []
            names = [t.get("name") for t in tool_list if isinstance(t, dict)]

        print("Available tools:")
        for name in names:
            print(" -", name)

        required = {"get_addresses", "search_products"}
        missing = required - set(names)

        if missing:
            print("\nWARNING: missing required tools:", ", ".join(sorted(missing)))
        else:
            print("\nRequired Instamart tools are available.")
    finally:
        mcp.close()

if __name__ == "__main__":
    main()
