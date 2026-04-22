"""Build Alation web UI URLs for browser navigation."""

from .credentials import load_credentials


def _base() -> str:
    creds = load_credentials("alation")
    return creds.get("base_url", "http://localhost:8000").rstrip("/")


# --- Catalog objects ---

def datasource_url(ds_id: int) -> str:
    return f"{_base()}/app/data/{ds_id}/overview"

def schema_url(schema_id: int) -> str:
    return f"{_base()}/app/schema/{schema_id}/overview"

def table_url(table_id: int) -> str:
    return f"{_base()}/app/table/{table_id}/overview"

def column_url(column_id: int) -> str:
    return f"{_base()}/app/attribute/{column_id}/overview"

def article_url(article_id: int) -> str:
    return f"{_base()}/article/{article_id}/"

def document_url(doc_id: int) -> str:
    return f"{_base()}/app/document/{doc_id}/overview"

def document_folder_url(folder_id: int) -> str:
    return f"{_base()}/app/doc-folder/{folder_id}/overview"

def bi_report_url(report_id: int) -> str:
    return f"{_base()}/app/bi_report/{report_id}/overview"

def bi_folder_url(folder_id: int) -> str:
    return f"{_base()}/app/bi_folder/{folder_id}/overview"

def bi_datasource_url(datasource_id: int) -> str:
    return f"{_base()}/app/bi_datasource/{datasource_id}/overview"

def query_url(query_id: int) -> str:
    return f"{_base()}/app/query/{query_id}/overview"


# --- Data products & marketplaces ---

def data_product_url(product_id: str) -> str:
    return f"{_base()}/app/data-product/{product_id}"

def marketplace_url(marketplace_id: str) -> str:
    return f"{_base()}/app/marketplace/{marketplace_id}"


# --- Alation AI Studio ---

def agent_url(agent_id: str) -> str:
    return f"{_base()}/app/studio/agents/a/{agent_id}"

def tool_url(tool_id: str) -> str:
    return f"{_base()}/app/studio/tools/{tool_id}"

def workflow_url(workflow_id: str) -> str:
    return f"{_base()}/app/studio/flows/{workflow_id}"
