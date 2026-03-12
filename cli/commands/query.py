"""Data product query commands."""

from cli.clients.base import print_json
from cli.clients.query import DataProductQueryClient, extract_schema_summary


def register(group_parsers):
    parser = group_parsers.add_parser("query", help="Query data products")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List data products")
    list_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    list_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    list_p.set_defaults(func=cmd_list)

    search_p = sub.add_parser("search", help="Search data products")
    search_p.add_argument("--query", "-q", required=True, help="Search query")
    search_p.add_argument("--marketplace", "-m", help="Marketplace ID (optional)")
    search_p.set_defaults(func=cmd_search)

    get_p = sub.add_parser("get", help="Get product details")
    get_p.add_argument("--product", "-p", required=True, help="Product ID")
    get_p.add_argument("--version", "-v", help="Specific version")
    get_p.add_argument("--schema-only", action="store_true", help="Return only schema summary")
    get_p.set_defaults(func=cmd_get)

    exec_p = sub.add_parser("execute", help="Execute SQL query")
    exec_p.add_argument("--product", "-p", required=True, help="Product ID")
    exec_p.add_argument("--sql", "-s", required=True, help="SQL query")
    exec_p.add_argument("--result-name", "-r", help="Result table name")
    exec_p.add_argument("--timeout", "-t", type=float, default=60, help="Timeout (seconds)")
    exec_p.add_argument("--no-fallback-auth", action="store_true", help="Disable fallback to default credentials")
    exec_p.set_defaults(func=cmd_execute)

    async_p = sub.add_parser("execute-async", help="Execute SQL as background task")
    async_p.add_argument("--product", "-p", required=True, help="Product ID")
    async_p.add_argument("--sql", "-s", required=True, help="SQL query")
    async_p.add_argument("--result-name", "-r", help="Result table name")
    async_p.set_defaults(func=cmd_execute_async)

    val_p = sub.add_parser("validate", help="Validate SQL without executing")
    val_p.add_argument("--product", "-p", required=True, help="Product ID")
    val_p.add_argument("--sql", "-s", required=True, help="SQL to validate")
    val_p.set_defaults(func=cmd_validate)


def cmd_list(args) -> int:
    with DataProductQueryClient() as client:
        result = client.list_products(limit=args.limit, offset=args.skip)
        print_json(result)
    return 0


def cmd_search(args) -> int:
    with DataProductQueryClient() as client:
        if args.marketplace:
            result = client.search_products(args.query, args.marketplace)
        else:
            all_products = client.list_products(limit=500)
            query_lower = args.query.lower()
            filtered = []
            for item in all_products.get("results", []):
                product_id = (item.get("product_id") or "").lower()
                name = (item.get("name") or "").lower()
                desc = (item.get("description") or "").lower()
                if query_lower in product_id or query_lower in name or query_lower in desc:
                    filtered.append(item)
            result = {"count": len(filtered), "results": filtered, "search_mode": "filter"}
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with DataProductQueryClient() as client:
        result = client.get_product(args.product, args.version)
        if args.schema_only:
            result = extract_schema_summary(result)
        print_json(result)
    return 0


def cmd_execute(args) -> int:
    with DataProductQueryClient() as client:
        result = client.execute_sql(
            args.product,
            args.sql,
            result_table_name=args.result_name,
            timeout_secs=args.timeout,
            allow_fallback_auth=not args.no_fallback_auth,
        )
        print_json(result)
    return 0


def cmd_execute_async(args) -> int:
    with DataProductQueryClient() as client:
        result = client.execute_sql_async(
            args.product,
            args.sql,
            result_table_name=args.result_name,
        )
        print_json(result)
    return 0


def cmd_validate(args) -> int:
    with DataProductQueryClient() as client:
        result = client.validate_sql(args.product, args.sql)
        print_json(result)
    return 0
