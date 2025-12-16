"""
Thin wrapper to run RealTimeX PyAutoGUI MCP server over stdio without banners/warnings.
"""

import warnings

# Silence deprecation and other warnings that would corrupt the stdio JSON stream.
warnings.filterwarnings("ignore")

import realtimex_pyautogui_server.server as srv


def main() -> None:
    # show_banner=False prevents ASCII art on stdout which breaks MCP handshake.
    srv.mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
