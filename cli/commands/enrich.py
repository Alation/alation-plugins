"""Catalog metadata enrichment commands."""

from cli.clients.base import print_json
from cli.clients.enrich import EnrichClient


def register(group_parsers):
    parser = group_parsers.add_parser("enrich", help="Enrich catalog metadata")
    sub = parser.add_subparsers(dest="command", required=True)

    lf_p = sub.add_parser("list-fields", help="List custom fields")
    lf_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    lf_p.set_defaults(func=cmd_list_fields)

    gv_p = sub.add_parser("get-values", help="Get field values for object")
    gv_p.add_argument("--otype", required=True, help="Object type (table, schema, etc)")
    gv_p.add_argument("--oid", type=int, required=True, help="Object ID")
    gv_p.set_defaults(func=cmd_get_values)

    sf_p = sub.add_parser("set-field", help="Set field value")
    sf_p.add_argument("--otype", required=True, help="Object type")
    sf_p.add_argument("--oid", type=int, required=True, help="Object ID")
    sf_p.add_argument("--field-id", type=int, required=True, help="Field ID")
    sf_p.add_argument("--value", required=True, help="Value to set")
    sf_p.set_defaults(func=cmd_set_field)


def cmd_list_fields(args) -> int:
    with EnrichClient() as client:
        result = client.list_custom_fields(limit=args.limit)
        print_json(result)
    return 0


def cmd_get_values(args) -> int:
    with EnrichClient() as client:
        result = client.get_field_values(args.otype, args.oid)
        print_json(result)
    return 0


def cmd_set_field(args) -> int:
    with EnrichClient() as client:
        result = client.set_field_value(args.otype, args.oid, args.field_id, args.value)
        print_json(result)
    return 0
