import json
from swiggy.client import MCPClient, unwrap_tool_result

def main():
    m=MCPClient()
    try:
        m.initialize()
        raw=unwrap_tool_result(m.call_tool('get_addresses', {'page':1,'pageSize':10}))
        data=raw.get('data',raw)
        addresses=data.get('addresses',[]) if isinstance(data,dict) else []
        print(json.dumps(addresses, indent=2, ensure_ascii=False))
        print('\nCopy the real address IDs into GitHub Secret SWIGGY_ADDRESS_MAP_JSON. Do not invent IDs.')
    finally: m.close()
if __name__=='__main__': main()
