"""Catalog search command."""

import json
import sys

from cli.clients.base import print_error, print_json
from cli.clients.search import SearchClient
from cli.commands._helpers import resolve_positional_or_flag


def register(group_parsers):
    # We use nargs="?" to support positional or flagged args (--query)
    parser = group_parsers.add_parser("search", help="Search the Alation catalog")
    parser.add_argument("query", nargs="?", help="Search query (optional; omit to browse by filter)")
    parser.add_argument("--query", "-q", dest="query_flag", help="Search query (optional)")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max results")
    parser.add_argument(
        "--type",
        "--otype",
        "-t",
        dest="types",
        action="append",
        help="""Filter by type (repeatable, e.g. --type table --type view). Accepted types are:
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
- bi_report (dashboard/report: Looker Dashboard, Power BI Report, Tableau Dashboard)
- bi_folder
- bi_datasource (semantic layer: Looker Explore, Power BI Dataset, Tableau Datasource)
- policy
- business_policy
- policy_group
    """,
    )
    parser.add_argument(
        "--filters",
        help='Raw JSON array of {"filter_id","filter_values"} objects. '
        "Resolve IDs with search-fields / search-values.",
    )
    parser.add_argument(
        "--ranges",
        help='Raw JSON array of {"field","start","end"} date-range objects '
        "(ISO YYYY-MM-DD; field = ts_updated, ts_created, or a custom DATE field id).",
    )
    parser.add_argument("--starred", action="store_true", help="Only bookmarked/starred items")
    parser.add_argument("--watching", action="store_true", help="Only watched items")
    parser.add_argument("--recent", action="store_true", help="Only recently-visited items")
    parser.add_argument(
        "--domain",
        dest="domains",
        action="append",
        help="Scope to a domain ID (repeatable)",
    )
    parser.set_defaults(func=cmd_search)

    fields_p = group_parsers.add_parser(
        "search-fields", help="Discover fields usable as search filters"
    )
    fields_p.add_argument("query", nargs="?", help="Term to match field names")
    fields_p.add_argument("--query", "-q", dest="query_flag", help="Term to match field names")
    fields_p.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    fields_p.set_defaults(func=cmd_search_fields)

    values_p = group_parsers.add_parser(
        "search-values", help="Resolve filter values (e.g. a data source name) to filter IDs"
    )
    values_p.add_argument("--field", "-f", required=True, help="Field ID (int custom field or built-in facet key like 'ds')")
    values_p.add_argument("query", nargs="?", help="Term to match values")
    values_p.add_argument("--query", "-q", dest="query_flag", help="Term to match values")
    values_p.add_argument("--builtin", action="store_true", help="Field is a built-in facet (is_builtin=True)")
    values_p.add_argument("--limit", "-l", type=int, default=10, help="Max results")
    values_p.set_defaults(func=cmd_search_values)


def _parse_json_arg(raw: str | None, label: str):
    """Parse a raw JSON array CLI argument, exiting 2 on invalid input."""
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print_error(f"--{label} must be valid JSON: {e}")
        sys.exit(2)
    if not isinstance(parsed, list):
        print_error(f"--{label} must be a JSON array, got {type(parsed).__name__}")
        sys.exit(2)
    return parsed


def cmd_search(args) -> int:
    # Query is optional: an empty term with filters browses the catalog, and
    # an empty term with no filters returns top results (like an empty UI search).
    query = args.query or args.query_flag or ""
    filters = _parse_json_arg(args.filters, "filters")
    ranges = _parse_json_arg(args.ranges, "ranges")
    with SearchClient() as client:
        result = client.search(
            query,
            limit=args.limit,
            object_types=args.types,
            filters=filters,
            ranges=ranges,
            starred=args.starred or None,
            watching=args.watching or None,
            recent=args.recent or None,
            domain_ids=args.domains,
        )
        print_json(result)
    return 0


def cmd_search_fields(args) -> int:
    query = resolve_positional_or_flag(args, "query", "query_flag", "query")
    with SearchClient() as client:
        result = client.search_filter_fields(query, limit=args.limit)
        print_json(result)
    return 0


def cmd_search_values(args) -> int:
    query = resolve_positional_or_flag(args, "query", "query_flag", "query")
    field_id: int | str = args.field
    if isinstance(field_id, str) and field_id.isdigit():
        field_id = int(field_id)
    with SearchClient() as client:
        result = client.search_filter_values(
            field_id, query, limit=args.limit, is_builtin=args.builtin
        )
        print_json(result)
    return 0
