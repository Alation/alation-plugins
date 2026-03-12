"""Data product configuration commands."""

import json

from cli.clients.base import print_error, print_json
from cli.clients.product import DataProductConfigClient
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("product", help="Manage data product specs")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List data products")
    list_p.add_argument("--limit", type=int, default=100, help="Max results")
    list_p.add_argument("--order-by", default="-ts_updated", help="Order by field (prefix with - for descending)")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get data product by ID")
    get_p.add_argument("product_id", help="Data product ID (e.g. finance:sales)")
    get_p.set_defaults(func=cmd_get)

    sub.add_parser("create", help="Create data product (read JSON spec from stdin)").set_defaults(func=cmd_create)
    sub.add_parser("update", help="Update data product (read JSON spec from stdin)").set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete data product")
    delete_p.add_argument("product_id", help="Data product ID")
    delete_p.set_defaults(func=cmd_delete)

    get_ver_p = sub.add_parser("get-version", help="Get data product version")
    get_ver_p.add_argument("product_id", help="Data product ID")
    get_ver_p.add_argument("version_id", help="Version ID (e.g. 1.0.0)")
    get_ver_p.set_defaults(func=cmd_get_version)

    upd_ver_p = sub.add_parser("update-version", help="Update data product version status")
    upd_ver_p.add_argument("product_id", help="Data product ID")
    upd_ver_p.add_argument("version_id", help="Version ID")
    upd_ver_p.add_argument("--status", required=True, choices=["draft", "ready"], help="New status for the version")
    upd_ver_p.set_defaults(func=cmd_update_version)

    del_ver_p = sub.add_parser("delete-version", help="Delete data product version")
    del_ver_p.add_argument("product_id", help="Data product ID")
    del_ver_p.add_argument("version_id", help="Version ID")
    del_ver_p.set_defaults(func=cmd_delete_version)

    check_p = sub.add_parser("check-standards", help="Check data product against standards")
    check_p.add_argument("--spec", required=True, help="Path to product spec JSON file")
    check_p.add_argument("--standards", required=True, help="Path to standards JSON array file")
    check_p.set_defaults(func=cmd_check_standards)


def cmd_list(args) -> int:
    with DataProductConfigClient() as client:
        result = client.list_products(limit=args.limit, order_by=args.order_by)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with DataProductConfigClient() as client:
        result = client.get_product(args.product_id)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    spec = read_json_stdin("product spec")
    if spec is None:
        return 1
    with DataProductConfigClient() as client:
        result = client.create_product(spec)
        print_json(result)
    return 0


def cmd_update(_args) -> int:
    spec = read_json_stdin("product spec")
    if spec is None:
        return 1
    with DataProductConfigClient() as client:
        result = client.update_product(spec)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with DataProductConfigClient() as client:
        client.delete_product(args.product_id)
        print_json({"status": "deleted", "product_id": args.product_id})
    return 0


def cmd_get_version(args) -> int:
    with DataProductConfigClient() as client:
        result = client.get_version(args.product_id, args.version_id)
        print_json(result)
    return 0


def cmd_update_version(args) -> int:
    with DataProductConfigClient() as client:
        result = client.update_version(args.product_id, args.version_id, args.status)
        print_json(result)
    return 0


def cmd_delete_version(args) -> int:
    with DataProductConfigClient() as client:
        client.delete_version(args.product_id, args.version_id)
        print_json({"status": "deleted", "product_id": args.product_id, "version_id": args.version_id})
    return 0


def cmd_check_standards(args) -> int:
    try:
        with open(args.spec) as f:
            product_spec = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print_error(f"Failed to read spec file: {e}")
        return 1
    try:
        with open(args.standards) as f:
            standards = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print_error(f"Failed to read standards file: {e}")
        return 1
    if not isinstance(standards, list):
        print_error("Standards file must contain a JSON array")
        return 1
    with DataProductConfigClient() as client:
        result = client.check_standards(product_spec, standards)
        print_json(result)
    return 0
