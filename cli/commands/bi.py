"""BI discovery commands — detail and cross-navigation."""

from cli.clients.base import print_error, print_json
from cli.clients.bi import BiClient


def register(group_parsers):
    parser = group_parsers.add_parser("bi", help="Browse BI reports and datasources")
    sub = parser.add_subparsers(dest="command", required=True)

    # describe
    desc_p = sub.add_parser("describe", help="Get detail for a BI object")
    desc_p.add_argument("--type", "-t", required=True, choices=["report", "datasource"])
    desc_p.add_argument("--id", type=int, required=True, help="Object ID")
    desc_p.set_defaults(func=cmd_describe)

    # report-sources
    rs_p = sub.add_parser("report-sources", help="Datasources upstream of a report")
    rs_p.add_argument("--id", type=int, required=True, help="BI report ID")
    rs_p.add_argument("--limit", "-l", type=int, default=100)
    rs_p.set_defaults(func=cmd_report_sources)

    # source-reports
    sr_p = sub.add_parser("source-reports", help="Reports downstream of a datasource")
    sr_p.add_argument("--id", type=int, required=True, help="BI datasource ID")
    sr_p.add_argument("--limit", "-l", type=int, default=100)
    sr_p.set_defaults(func=cmd_source_reports)

    # product-spec
    ps_p = sub.add_parser("product-spec", help="Generate data product spec (YAML) from a BI datasource")
    ps_p.add_argument("--id", type=int, required=True, help="BI datasource ID")
    ps_p.set_defaults(func=cmd_product_spec)


def cmd_describe(args) -> int:
    with BiClient() as client:
        if args.type == "report":
            result = client.get_report(args.id)
        elif args.type == "datasource":
            result = client.get_datasource_views(args.id)
        else:
            print_error(f"Unknown type: {args.type}")
            return 1
        print_json(result)
    return 0


def cmd_report_sources(args) -> int:
    with BiClient() as client:
        result = client.report_datasources(report_id=args.id, limit=args.limit)
        print_json(result)
    return 0


def cmd_source_reports(args) -> int:
    with BiClient() as client:
        result = client.datasource_reports(datasource_id=args.id, limit=args.limit)
        print_json(result)
    return 0


def cmd_product_spec(args) -> int:
    with BiClient() as client:
        result = client.get_product_spec(args.id)
        if not result:
            print_error(
                f"Could not generate product spec for datasource {args.id}. "
                "This may not be supported for this BI server type yet."
            )
            return 1
        print(result)
    return 0
