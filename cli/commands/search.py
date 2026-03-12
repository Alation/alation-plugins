"""Catalog search command."""

from cli.clients.base import print_json
from cli.clients.search import SearchClient


def register(group_parsers):
    parser = group_parsers.add_parser("search", help="Search the Alation catalog")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max results")
    parser.add_argument("--type", "-t", help="""Filter by type. Accepted types are:
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
    """)
    parser.set_defaults(func=cmd_search)


def cmd_search(args) -> int:
    object_types = [args.type] if args.type else None
    with SearchClient() as client:
        result = client.search(
            args.query,
            limit=args.limit,
            object_types=object_types,
        )
        print_json(result)
    return 0
