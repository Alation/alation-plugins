"""Workflow schedule management commands."""

from cli.clients.base import print_error, print_json
from cli.clients.workflow import WorkflowAPIClient
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("schedule", help="Manage workflow schedules")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List schedules")
    list_p.add_argument("--workflow-id", help="Filter by workflow ID")
    list_p.add_argument("--limit", type=int, default=100, help="Max results")
    list_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get schedule by ID")
    get_p.add_argument("id", help="Schedule ID")
    get_p.set_defaults(func=cmd_get)

    create_p = sub.add_parser("create", help="Create schedule")
    create_p.add_argument("--workflow-id", required=True, help="Workflow ID")
    create_p.add_argument("--name", required=True, help="Schedule name")
    create_p.add_argument("--cron", required=True, help="Cron expression (e.g., '0 9 * * 1' for Monday 9am)")
    create_p.add_argument("--timezone", default="America/Los_Angeles", help="Timezone")
    create_p.add_argument("--timeout", type=int, default=60, help="Timeout in minutes")
    create_p.add_argument("--disabled", action="store_true", help="Create in disabled state")
    create_p.set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update schedule from stdin JSON")
    update_p.add_argument("id", help="Schedule ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete schedule")
    delete_p.add_argument("id", help="Schedule ID")
    delete_p.set_defaults(func=cmd_delete)

    enable_p = sub.add_parser("enable", help="Enable schedule")
    enable_p.add_argument("id", help="Schedule ID")
    enable_p.set_defaults(func=cmd_enable)

    disable_p = sub.add_parser("disable", help="Disable schedule")
    disable_p.add_argument("id", help="Schedule ID")
    disable_p.set_defaults(func=cmd_disable)


def cmd_list(args) -> int:
    with WorkflowAPIClient() as client:
        result = client.list_schedules(workflow_id=args.workflow_id, limit=args.limit, offset=args.skip)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with WorkflowAPIClient() as client:
        result = client.get_schedule(args.id)
        print_json(result)
    return 0


def cmd_create(args) -> int:
    with WorkflowAPIClient() as client:
        auth_config = client.get_managed_auth_config()
        if not auth_config:
            print_error("No MANAGED auth config found. Set up OAuth first via the Alation AI UI.")
            return 1

        schedule = {
            "workflow_id": args.workflow_id,
            "schedule_name": args.name,
            "cron_schedule": args.cron,
            "timezone": args.timezone,
            "auth_config_id": auth_config["id"],
            "workflow_parameters": {},
            "concurrency_policy": "forbid",
            "timeout_minutes": args.timeout,
            "enabled": not args.disabled,
        }

        result = client.create_schedule(schedule)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    schedule = read_json_stdin("schedule config")
    if schedule is None:
        return 1
    with WorkflowAPIClient() as client:
        result = client.update_schedule(args.id, schedule)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with WorkflowAPIClient() as client:
        client.delete_schedule(args.id)
        print(f"Deleted schedule: {args.id}")
    return 0


def cmd_enable(args) -> int:
    with WorkflowAPIClient() as client:
        result = client.enable_schedule(args.id)
        print(f"Enabled schedule: {args.id}")
        print(f"Next run: {result.get('next_run_at')}")
    return 0


def cmd_disable(args) -> int:
    with WorkflowAPIClient() as client:
        client.disable_schedule(args.id)
        print(f"Disabled schedule: {args.id}")
    return 0
