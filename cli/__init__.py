"""Alation platform CLI — query data, manage agents, automate workflows, and more."""

import argparse
import sys

from cli.clients.base import AuthenticationError, print_error


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="alation",
        description="Alation platform CLI — query data, manage agents, automate workflows, and more.",
    )
    group_parsers = parser.add_subparsers(dest="group", required=True)

    from cli.commands import (
        agent,
        bi,
        browse,
        chat,
        datasource,
        enrich,
        llm,
        marketplace,
        product,
        query,
        schedule,
        search,
        setup,
        tool,
        workflow,
    )

    for mod in [
        query,
        chat,
        agent,
        tool,
        llm,
        datasource,
        browse,
        bi,
        search,
        workflow,
        schedule,
        product,
        marketplace,
        enrich,
        setup,
    ]:
        mod.register(group_parsers)

    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130
    except Exception as e:  # noqa: BLE001
        if isinstance(e, AuthenticationError):
            print_error(f"AUTH_ERROR: {e}")
            print_error(
                "Run 'python -m cli setup check' to diagnose, "
                "or use the setup skill to re-authenticate."
            )
            return 2
        print_error(str(e))
        return 1
