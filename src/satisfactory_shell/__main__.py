"""Entry point: ``python -m satisfactory_shell`` / ``satisfactory-shell`` / frozen exe."""

from __future__ import annotations

import argparse
import logging
import sys

import uvicorn


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="satisfactory-shell")
    parser.add_argument("--host", help="override webui.host")
    parser.add_argument("--port", type=int, help="override webui.port")
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="do not launch the dedicated server on startup",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help=(
            "run first-run claim if bootstrap.json exists in the user config "
            "directory (also happens without this flag)"
        ),
    )
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    from .app import create_app  # pylint: disable=import-outside-toplevel
    from .configs.settings import load  # pylint: disable=import-outside-toplevel

    cfg = load()
    if args.no_auto_start:
        cfg.process.auto_start = False
    if args.bootstrap:
        logging.getLogger("satisfactory_shell").info(
            "bootstrap flag set; claim runs if bootstrap.json is present"
        )
    app = create_app(cfg)
    host = args.host or cfg.webui_host
    port = args.port or cfg.webui_port
    logging.getLogger("satisfactory_shell").info(
        "WebUI on http://%s:%s (config: %s)", host, port, cfg.file
    )
    uvicorn.run(app, host=host, port=port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    sys.exit(main())
