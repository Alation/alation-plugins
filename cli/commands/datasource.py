"""Data source management commands."""

from cli.clients.base import print_json
from cli.clients.admin import AdminClient
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("datasource", help="Manage data source connections")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List data sources")
    list_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get data source details")
    get_p.add_argument("ds_id", type=int, help="Data source ID")
    get_p.set_defaults(func=cmd_get)

    sub.add_parser("create", help="Create data source (JSON stdin)").set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update data source (JSON stdin)")
    update_p.add_argument("ds_id", type=int, help="Data source ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete data source")
    delete_p.add_argument("ds_id", type=int, help="Data source ID")
    delete_p.set_defaults(func=cmd_delete)


def cmd_list(args) -> int:
    with AdminClient() as client:
        result = client.list_datasources(limit=args.limit)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with AdminClient() as client:
        result = client.get_datasource(args.ds_id)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    spec = read_json_stdin("datasource config")
    if spec is None:
        return 1
    with AdminClient() as client:
        result = client.create_datasource(spec)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    spec = read_json_stdin("datasource config")
    if spec is None:
        return 1
    with AdminClient() as client:
        result = client.update_datasource(args.ds_id, spec)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with AdminClient() as client:
        client.delete_datasource(args.ds_id)
        print_json({"status": "deleted", "ds_id": args.ds_id})
    return 0
