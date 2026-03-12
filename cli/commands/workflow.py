"""Workflow management commands."""

import json
from pathlib import Path

from cli.clients.base import print_json, print_error
from cli.clients.workflow import WorkflowAPIClient
from cli.commands._helpers import read_json_stdin

_PLUGIN_ROOT = Path(__file__).parent.parent.parent  # cli/commands/ -> cli/ -> alation/
TEMPLATES_DIR = _PLUGIN_ROOT / "skills" / "automate" / "references" / "templates"


def load_template(name: str) -> dict:
    """Load a workflow template by name."""
    template_path = TEMPLATES_DIR / f"{name}.json"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {name}")
    return json.loads(template_path.read_text())


def _list_templates() -> list[str]:
    """List available template names."""
    if not TEMPLATES_DIR.exists():
        return []
    return [p.stem for p in TEMPLATES_DIR.glob("*.json")]


def build_workflow_from_template(
    template_name: str,
    name: str,
    description: str | None = None,
    agent_id: str | None = None,
    tool_id: str | None = None,
    data_product_id: str | None = None,
    query: str | None = None,
    email: str | None = None,
    subject: str | None = None,
) -> dict:
    """Build a workflow from a template with substitutions."""
    template = load_template(template_name)

    workflow = {
        "name": name,
        "description": description or template.get("description", ""),
        "definition": template["definition"],
    }

    for node in workflow["definition"]["nodes"]:
        node_data = node.get("data", {})
        config = node_data.get("config", {})
        inputs = node_data.get("inputs", {})

        if agent_id and config.get("agent_id") == "{{AGENT_ID}}":
            config["agent_id"] = agent_id

        if tool_id and config.get("tool_id") == "{{TOOL_ID}}":
            config["tool_id"] = tool_id

        for key, val in inputs.items():
            if isinstance(val, dict) and val.get("type") == "static":
                if val.get("value") == "{{DATA_PRODUCT_ID}}" and data_product_id:
                    val["value"] = data_product_id
                elif val.get("value") == "{{QUERY}}" and query:
                    val["value"] = query
                elif val.get("value") == "{{EMAIL}}" and email:
                    val["value"] = email
                elif val.get("value") == "{{SUBJECT}}" and subject:
                    val["value"] = subject

    return workflow


def register(group_parsers):
    parser = group_parsers.add_parser("workflow", help="Manage workflows")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List workflows")
    list_p.add_argument("--limit", type=int, default=100, help="Max results")
    list_p.add_argument("--skip", "-s", type=int, default=0, help="Skip N results")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get workflow by ID")
    get_p.add_argument("id", help="Workflow ID")
    get_p.set_defaults(func=cmd_get)

    create_p = sub.add_parser("create", help="Create workflow from stdin JSON or template")
    create_p.add_argument("--from-template", help="Use template (e.g., query-and-email)")
    create_p.add_argument("--name", help="Workflow name (required with --from-template)")
    create_p.add_argument("--description", help="Workflow description")
    create_p.add_argument("--agent-id", help="Agent ID for template")
    create_p.add_argument("--tool-id", help="Tool ID for template")
    create_p.add_argument("--data-product-id", help="Data product ID for template")
    create_p.add_argument("--query", help="Query message for template")
    create_p.add_argument("--email", help="Email recipient for template")
    create_p.add_argument("--subject", help="Email subject for template")
    create_p.set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update workflow from stdin JSON")
    update_p.add_argument("id", help="Workflow ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete workflow")
    delete_p.add_argument("id", help="Workflow ID")
    delete_p.set_defaults(func=cmd_delete)

    exec_p = sub.add_parser("execute", help="Execute workflow")
    exec_p.add_argument("id", help="Workflow ID")
    exec_p.add_argument("--dry-run", action="store_true", help="Validate without executing")
    exec_p.add_argument("--verbose", "-v", action="store_true", help="Show output details")
    exec_p.set_defaults(func=cmd_execute)

    sub.add_parser("validate", help="Validate workflow from stdin JSON").set_defaults(func=cmd_validate)

    sub.add_parser("templates", help="List workflow templates").set_defaults(func=cmd_templates)

    show_tpl_p = sub.add_parser("show-template", help="Show workflow template")
    show_tpl_p.add_argument("name", help="Template name")
    show_tpl_p.set_defaults(func=cmd_show_template)

    sub.add_parser("auth-configs", help="List auth configs for scheduling").set_defaults(func=cmd_auth_configs)


def cmd_list(args) -> int:
    with WorkflowAPIClient() as client:
        result = client.list_workflows(limit=args.limit, offset=args.skip)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with WorkflowAPIClient() as client:
        result = client.get_workflow(args.id)
        print_json(result)
    return 0


def cmd_create(args) -> int:
    if args.from_template:
        if not args.name:
            print_error("--name is required when using --from-template")
            return 1
        workflow = build_workflow_from_template(
            template_name=args.from_template,
            name=args.name,
            description=args.description,
            agent_id=args.agent_id,
            tool_id=args.tool_id,
            data_product_id=args.data_product_id,
            query=args.query,
            email=args.email,
            subject=args.subject,
        )
    else:
        workflow = read_json_stdin("workflow config")
        if workflow is None:
            return 1

    with WorkflowAPIClient() as client:
        result = client.create_workflow(workflow)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    workflow = read_json_stdin("workflow config")
    if workflow is None:
        return 1
    with WorkflowAPIClient() as client:
        result = client.update_workflow(args.id, workflow)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with WorkflowAPIClient() as client:
        client.delete_workflow(args.id)
        print(f"Deleted workflow: {args.id}")
    return 0


def cmd_execute(args) -> int:
    with WorkflowAPIClient() as client:
        status = "unknown"

        for event in client.execute_workflow(args.id, dry_run=args.dry_run):
            event_type = event.get("type", "")
            node_id = event.get("node_id", "")
            message = event.get("message", "")

            if event_type == "workflow_started":
                execution_id = event.get("execution_id")
                if args.dry_run:
                    print("DRY RUN - Validating workflow...")
                else:
                    print(f"Started execution: {execution_id}")

            elif event_type == "node_started":
                print(f"  [{node_id}] Running...")

            elif event_type == "node_completed":
                print(f"  [{node_id}] Done")
                if args.verbose:
                    output = event.get("data", {}).get("output", {})
                    if output:
                        print(f"    Output keys: {list(output.keys())}")

            elif event_type == "node_failed":
                error = event.get("data", {}).get("error", message)
                print(f"  [{node_id}] FAILED: {error[:200]}")
                status = "failed"

            elif event_type == "workflow_completed":
                status = "completed"
                print("\nWorkflow completed successfully")

            elif event_type == "workflow_failed":
                status = "failed"
                error = event.get("data", {}).get("error", message)
                print(f"\nWorkflow failed: {error[:200]}")

            elif event_type == "validation_result" and args.dry_run:
                valid = event.get("data", {}).get("valid", False)
                errors = event.get("data", {}).get("errors", [])
                if valid:
                    print("Validation passed")
                else:
                    print(f"Validation failed: {errors}")

        return 0 if status == "completed" else 1


def cmd_validate(_args) -> int:
    workflow = read_json_stdin("workflow config")
    if workflow is None:
        return 1
    with WorkflowAPIClient() as client:
        result = client.validate_workflow(workflow)
        print_json(result)
        return 0 if result.get("valid", True) else 1


def cmd_templates(_args) -> int:
    templates = _list_templates()
    if not templates:
        print("No templates found")
        return 0
    print("Available templates:")
    for name in sorted(templates):
        template = load_template(name)
        desc = template.get("description", "")[:60]
        print(f"  {name}: {desc}")
    return 0


def cmd_show_template(args) -> int:
    try:
        template = load_template(args.name)
        print_json(template)
    except FileNotFoundError:
        print_error(f"Template not found: {args.name}")
        print_error(f"Available: {', '.join(_list_templates())}")
        return 1
    return 0


def cmd_auth_configs(_args) -> int:
    with WorkflowAPIClient() as client:
        configs = client.list_auth_configs()
        print_json(configs)
    return 0
