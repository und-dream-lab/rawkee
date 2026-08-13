"""
Start the RawKee X3D MCP server.

    python -m rawkee.mcp [--host HOST] [--port PORT]

Defaults: host=0.0.0.0  port=8766
MCP endpoint: http://localhost:8766/mcp
"""
import argparse
from rawkee.mcp.RKMCPServer import run


def main():
    p = argparse.ArgumentParser(
        description='RawKee X3D MCP Server — X3D scene building and validation via MCP')
    p.add_argument('--host', default='0.0.0.0',
                   help='Bind host (default: 0.0.0.0)')
    p.add_argument('--port', type=int, default=8766,
                   help='Listen port (default: 8766)')
    args = p.parse_args()
    run(args.host, args.port)


if __name__ == '__main__':
    main()
