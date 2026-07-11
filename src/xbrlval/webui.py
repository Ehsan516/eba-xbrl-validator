"""launcher for the local web UI."""

from __future__ import annotations

import webbrowser
from threading import Timer


def main(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    import uvicorn

    from xbrlval.api import app

    if open_browser:
        Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
