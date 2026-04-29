"""Agent configuration commands."""

from cli.clients.base import print_json
from cli.clients.config import ConfigAPIClient, _extract_items
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("agent", help="Manage agent configurations")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List agent configs")
    list_p.add_argument("--visibility", choices=["featured", "regular", "advanced"], help="Filter by visibility label")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get agent config by ID")
    get_p.add_argument("id", help="Agent config ID")
    get_p.set_defaults(func=cmd_get)

    get_default_p = sub.add_parser("get-default", help="Get default agent config by reference")
    get_default_p.add_argument("ref", help="Default agent reference (e.g., sql_query_agent)")
    get_default_p.set_defaults(func=cmd_get_default)

    sub.add_parser("create", help="Create agent config (read JSON from stdin)").set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update agent config (read JSON from stdin)")
    update_p.add_argument("id", help="Agent config ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete agent config")
    delete_p.add_argument("id", help="Agent config ID")
    delete_p.set_defaults(func=cmd_delete)

    clone_p = sub.add_parser("clone", help="Clone agent config")
    clone_p.add_argument("id", help="Agent config ID to clone")
    clone_p.set_defaults(func=cmd_clone)

    publish_p = sub.add_parser("publish", help="Publish agent as a callable tool")
    publish_p.add_argument("id", help="Agent config ID")
    publish_p.set_defaults(func=cmd_publish)

    unpublish_p = sub.add_parser("unpublish", help="Unpublish agent's tool")
    unpublish_p.add_argument("id", help="Agent config ID")
    unpublish_p.set_defaults(func=cmd_unpublish)


def _summarize_agent(agent: dict) -> dict:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "description": agent.get("description"),
        "is_default": agent.get("is_default", False),
        "default_ref": agent.get("default_ref"),
        "url": agent.get("url"),
    }


def cmd_list(args) -> int:
    visibility_labels = [args.visibility] if args.visibility else None
    with ConfigAPIClient() as client:
        result = client.list_agents(visibility_labels=visibility_labels)
        agents = _extract_items(result)
        print_json([_summarize_agent(a) for a in agents])
    return 0


def cmd_get(args) -> int:
    with ConfigAPIClient() as client:
        result = client.get_agent(args.id)
        print_json(result)
    return 0


def cmd_get_default(args) -> int:
    with ConfigAPIClient() as client:
        result = client.get_default_agent(args.ref)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    config = read_json_stdin("agent config")
    if config is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.create_agent(config)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    updates = read_json_stdin("agent config")
    if updates is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.update_agent(args.id, updates)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with ConfigAPIClient() as client:
        client.delete_agent(args.id)
        print(f"Deleted agent config: {args.id}")
    return 0


def cmd_clone(args) -> int:
    with ConfigAPIClient() as client:
        result = client.clone_agent(args.id)
        print_json(result)
    return 0


def cmd_publish(args) -> int:
    with ConfigAPIClient() as client:
        result = client.publish_agent_as_tool(args.id)
        print_json(result)
    return 0


def cmd_unpublish(args) -> int:
    with ConfigAPIClient() as client:
        client.unpublish_agent_tool(args.id)
        print(f"Unpublished agent tool: {args.id}")
    return 0
