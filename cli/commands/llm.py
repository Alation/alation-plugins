"""LLM configuration and credentials commands."""

from cli.clients.base import print_json
from cli.clients.config import ConfigAPIClient
from cli.commands._helpers import read_json_stdin


def register(group_parsers):
    parser = group_parsers.add_parser("llm", help="Manage LLM configs and credentials")
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List LLM configs")
    list_p.add_argument("--credentials-id", help="Filter by credentials ID (for BYOM configs)")
    list_p.set_defaults(func=cmd_list)

    get_p = sub.add_parser("get", help="Get LLM config by ID")
    get_p.add_argument("id", help="LLM config ID")
    get_p.set_defaults(func=cmd_get)

    sub.add_parser("create", help="Create LLM config (read JSON from stdin)").set_defaults(func=cmd_create)

    update_p = sub.add_parser("update", help="Update LLM config (read JSON from stdin)")
    update_p.add_argument("id", help="LLM config ID")
    update_p.set_defaults(func=cmd_update)

    delete_p = sub.add_parser("delete", help="Delete LLM config")
    delete_p.add_argument("id", help="LLM config ID")
    delete_p.set_defaults(func=cmd_delete)

    # Credentials commands
    sub.add_parser("creds-list", help="List LLM credentials").set_defaults(func=cmd_creds_list)

    cg_p = sub.add_parser("creds-get", help="Get LLM credentials by ID")
    cg_p.add_argument("id", help="Credentials ID")
    cg_p.set_defaults(func=cmd_creds_get)

    sub.add_parser("creds-create", help="Create LLM credentials (read JSON from stdin)").set_defaults(func=cmd_creds_create)

    cu_p = sub.add_parser("creds-update", help="Update LLM credentials (read JSON from stdin)")
    cu_p.add_argument("id", help="Credentials ID")
    cu_p.set_defaults(func=cmd_creds_update)

    cd_p = sub.add_parser("creds-delete", help="Delete LLM credentials")
    cd_p.add_argument("id", help="Credentials ID")
    cd_p.set_defaults(func=cmd_creds_delete)

    cv_p = sub.add_parser("creds-validate", help="Validate LLM credentials")
    cv_p.add_argument("id", help="Credentials ID")
    cv_p.add_argument("--provider", required=True, help="LLM provider (openai, bedrock, azure, etc.)")
    cv_p.add_argument("--model", help="Optional model name to validate specific model")
    cv_p.set_defaults(func=cmd_creds_validate)


def cmd_list(args) -> int:
    with ConfigAPIClient() as client:
        result = client.list_llms(llm_credentials_id=args.credentials_id)
        print_json(result)
    return 0


def cmd_get(args) -> int:
    with ConfigAPIClient() as client:
        result = client.get_llm(args.id)
        print_json(result)
    return 0


def cmd_create(_args) -> int:
    config = read_json_stdin("LLM config")
    if config is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.create_llm(config)
        print_json(result)
    return 0


def cmd_update(args) -> int:
    updates = read_json_stdin("LLM config")
    if updates is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.update_llm(args.id, updates)
        print_json(result)
    return 0


def cmd_delete(args) -> int:
    with ConfigAPIClient() as client:
        client.delete_llm(args.id)
        print(f"Deleted LLM config: {args.id}")
    return 0


def cmd_creds_list(_args) -> int:
    with ConfigAPIClient() as client:
        result = client.list_credentials()
        print_json(result)
    return 0


def cmd_creds_get(args) -> int:
    with ConfigAPIClient() as client:
        result = client.get_credentials(args.id)
        print_json(result)
    return 0


def cmd_creds_create(_args) -> int:
    config = read_json_stdin("LLM credentials")
    if config is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.create_credentials(config)
        print_json(result)
    return 0


def cmd_creds_update(args) -> int:
    updates = read_json_stdin("LLM credentials")
    if updates is None:
        return 1
    with ConfigAPIClient() as client:
        result = client.update_credentials(args.id, updates)
        print_json(result)
    return 0


def cmd_creds_delete(args) -> int:
    with ConfigAPIClient() as client:
        client.delete_credentials(args.id)
        print(f"Deleted LLM credentials: {args.id}")
    return 0


def cmd_creds_validate(args) -> int:
    with ConfigAPIClient() as client:
        result = client.validate_credentials(args.id, args.provider, model_name=args.model)
        print_json(result)
    return 0
