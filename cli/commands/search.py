"""Catalog search command."""

from cli.clients.base import print_json
from cli.clients.search import SearchClient
from cli.commands._helpers import resolve_positional_or_flag


def register(group_parsers):
    # We use nargs="?" to support positional or flagged args (--query)
    parser = group_parsers.add_parser("search", help="Search the Alation catalog")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--query", "-q", dest="query_flag", help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max results")
    parser.add_argument(
        "--type",
        "--otype",
        "-t",
        help="""Filter by type. Accepted types are:
- table
- procedure
- function
- api_resource
- api_resource_field
- api_resource_folder
- article
- bi_field
- catalog_set
- column
- dataflow
- datasource
- doc_schema
- docstore_collection
- docstore_folder
- domain
- execution_result
- file
- filesystem
- glossary
- glossary_term
- glossary_v3
- group
- query_or_statement
- report_collection
- report_datasource
- report_object
- report_source
- schema
- tag
- thread
- conversation
- user
- value
- query
- documentation
- bi_report
- bi_folder
- policy
- business_policy
- policy_group
    """,
    )
    parser.set_defaults(func=cmd_search)


def cmd_search(args) -> int:
    query = resolve_positional_or_flag(args, "query", "query_flag", "query")
    object_types = [args.type] if args.type else None
    with SearchClient() as client:
        result = client.search(
            query,
            limit=args.limit,
            object_types=object_types,
        )
        print_json(result)
    return 0
