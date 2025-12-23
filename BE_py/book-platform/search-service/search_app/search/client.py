import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch

load_dotenv()


def get_os_client() -> OpenSearch:
    host = os.getenv("OPENSEARCH_HOST", "localhost")
    port = int(os.getenv("OPENSEARCH_PORT", "9200"))
    user = os.getenv("OPENSEARCH_USER", "admin")
    pwd = os.getenv("OPENSEARCH_PASSWORD", "")
    use_ssl = os.getenv("OPENSEARCH_USE_SSL", "true").lower() == "true"
    verify = os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() == "true"

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, pwd),
        use_ssl=use_ssl,
        verify_certs=verify,
        ssl_show_warn=False
    )
