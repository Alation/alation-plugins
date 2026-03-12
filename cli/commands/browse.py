"""Browse data source hierarchy commands."""

from cli.clients.base import print_error, print_json
from cli.clients.browse import BrowseClient


def register(group_parsers):
    parser = group_parsers.add_parser("browse", help="Browse data source hierarchies")
    sub = parser.add_subparsers(dest="command", required=True)

    # sources
    ls_p = sub.add_parser("sources", help="List data sources")
    ls_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    ls_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    ls_p.set_defaults(func=cmd_sources)

    # schemas
    lsc_p = sub.add_parser("schemas", help="List schemas in a data source")
    lsc_p.add_argument("--ds-id", type=int, required=True, help="Data source ID")
    lsc_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    lsc_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    lsc_p.set_defaults(func=cmd_schemas)

    # tables
    lt_p = sub.add_parser("tables", help="List tables")
    lt_p.add_argument("--schema-id", type=int, help="Schema ID")
    lt_p.add_argument("--ds-id", type=int, help="Data source ID (alternative to schema-id)")
    lt_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    lt_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    lt_p.set_defaults(func=cmd_tables)

    # columns
    lc_p = sub.add_parser("columns", help="List columns")
    lc_p.add_argument("--table-id", type=int, help="Table ID")
    lc_p.add_argument("--ds-id", type=int, help="Data source ID (alternative to table-id)")
    lc_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    lc_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    lc_p.set_defaults(func=cmd_columns)

    # describe
    desc_p = sub.add_parser("describe", help="Get details of an object")
    desc_p.add_argument("--type", "-t", required=True, choices=["datasource", "schema", "table", "column"], help="Object type")
    desc_p.add_argument("--id", type=int, required=True, help="Object ID")
    desc_p.set_defaults(func=cmd_describe)

    # tree
    tree_p = sub.add_parser("tree", help="Get hierarchical view of data source")
    tree_p.add_argument("--ds-id", type=int, required=True, help="Data source ID")
    tree_p.add_argument("--depth", "-d", type=int, default=2, choices=[1, 2, 3], help="1=schemas, 2=+tables, 3=+columns")
    tree_p.set_defaults(func=cmd_tree)


def cmd_sources(args) -> int:
    with BrowseClient() as client:
        result = client.list_datasources(limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_schemas(args) -> int:
    with BrowseClient() as client:
        result = client.list_schemas(args.ds_id, limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_tables(args) -> int:
    with BrowseClient() as client:
        result = client.list_tables(ds_id=args.ds_id, schema_id=args.schema_id, limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_columns(args) -> int:
    with BrowseClient() as client:
        result = client.list_columns(table_id=args.table_id, ds_id=args.ds_id, limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_describe(args) -> int:
    with BrowseClient() as client:
        if args.type == "datasource":
            result = client.get_datasource(args.id)
        elif args.type == "schema":
            result = client.get_schema(args.id)
        elif args.type == "table":
            result = client.get_table(args.id)
        elif args.type == "column":
            result = client.get_column(args.id)
        else:
            print_error(f"Unknown type: {args.type}")
            return 1
        print_json(result)
    return 0


def cmd_tree(args) -> int:
    with BrowseClient() as client:
        result = client.get_tree(args.ds_id, depth=args.depth)
        print_json(result)
    return 0
