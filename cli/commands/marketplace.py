"""Marketplace management commands."""

from cli.clients.base import print_json
from cli.clients.marketplace import MarketplaceClient
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("marketplace", help="Manage data marketplaces")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List all marketplaces")
    list_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    list_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get marketplace details")
    get_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    get_p.set_defaults(func=cmd_get)

    sub.add_parser("create", help="Create marketplace (JSON from stdin)").set_defaults(func=cmd_create)
    sub.add_parser("update", help="Update marketplace (JSON from stdin)").set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete a marketplace")
    delete_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    delete_p.set_defaults(func=cmd_delete)

    lp_p = sub.add_parser("products", help="List products in a marketplace")
    lp_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    lp_p.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    lp_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    lp_p.set_defaults(func=cmd_products)

    pub_p = sub.add_parser("publish", help="Publish a product to a marketplace")
    pub_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    pub_p.add_argument("--product", "-p", required=True, help="Product ID")
    pub_p.add_argument("--version", "-v", help="Specific version to publish")
    pub_p.set_defaults(func=cmd_publish)

    unpub_p = sub.add_parser("unpublish", help="Unpublish a product from a marketplace")
    unpub_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    unpub_p.add_argument("--product", "-p", required=True, help="Product ID")
    unpub_p.set_defaults(func=cmd_unpublish)

    search_p = sub.add_parser("search", help="Search products in a marketplace")
    search_p.add_argument("--marketplace", "-m", required=True, help="External marketplace ID")
    search_p.add_argument("--query", "-q", required=True, help="Search query")
    search_p.set_defaults(func=cmd_search)


def cmd_list(args) -> int:
    with MarketplaceClient() as client:
        result = client.list_marketplaces(limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with MarketplaceClient() as client:
        result = client.get_marketplace(args.marketplace)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    spec = read_json_stdin("marketplace spec")
    if spec is None:
        return 1
    with MarketplaceClient() as client:
        result = client.create_marketplace(spec)
        print_json(result)
    return 0


def cmd_update(_args) -> int:
    spec = read_json_stdin("marketplace spec")
    if spec is None:
        return 1
    with MarketplaceClient() as client:
        result = client.update_marketplace(spec)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with MarketplaceClient() as client:
        client.delete_marketplace(args.marketplace)
        print_json({"status": "deleted", "marketplace_id": args.marketplace})
    return 0


def cmd_products(args) -> int:
    with MarketplaceClient() as client:
        result = client.list_products(args.marketplace, limit=args.limit, skip=args.skip)
        print_json(result)
    return 0


def cmd_publish(args) -> int:
    with MarketplaceClient() as client:
        result = client.publish_product(args.marketplace, args.product, version=args.version)
        print_json(result)
    return 0


def cmd_unpublish(args) -> int:
    with MarketplaceClient() as client:
        client.unpublish_product(args.marketplace, args.product)
        print_json({"status": "unpublished", "marketplace_id": args.marketplace, "product_id": args.product})
    return 0


def cmd_search(args) -> int:
    with MarketplaceClient() as client:
        result = client.search_products(args.marketplace, args.query)
        print_json(result)
    return 0
