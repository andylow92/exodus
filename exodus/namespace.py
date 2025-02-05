# /exodus/exodus/namespace.py  

import logging
from typing import List, Optional
import requests

def make_headers(token: str, namespace: Optional[str] = None) -> dict:
    """Consistent with your existing make_headers in kv_migrator"""
    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace
    return headers

def list_namespaces(
    vault_addr: str,
    token: str,
    base_namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None
) -> List[str]:
    """
    Recursively list all child namespaces under the specified base_namespace.

    Args:
        vault_addr: Vault server address (e.g., "https://127.0.0.1:8200")
        token: Vault token with list/read permissions on sys/namespaces
        base_namespace: The namespace scope to list under (empty for root)
        verify: Whether to verify SSL certificates
        session: Optional requests.Session for connection reuse
    """
    if session is None:
        session = requests.Session()

    headers = make_headers(token, base_namespace)
    url = f"{vault_addr}/v1/sys/namespaces"

    try:
        resp = session.request(
            method="LIST",
            url=url,
            headers=headers,
            verify=verify
        )
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        return []

    if resp.status_code == 200:
        try:
            keys = resp.json().get("data", {}).get("keys", [])
        except ValueError as e:
            logging.error(f"Invalid JSON response: {str(e)}")
            return []
    else:
        logging.warning(
            f"Error listing namespaces under '{base_namespace}': "
            f"HTTP {resp.status_code} - {resp.text}"
        )
        return []

    all_namespaces: List[str] = []
    
    for key in keys:
        sub_ns = key.rstrip("/")
        new_namespace = (
            f"{base_namespace}/{sub_ns}" if base_namespace and sub_ns else sub_ns
        )
        all_namespaces.append(new_namespace)

        # Recursively gather child namespaces
        child_namespaces = list_namespaces(
            vault_addr=vault_addr,
            token=token,
            base_namespace=new_namespace,
            verify=verify,
            session=session
        )
        all_namespaces.extend(child_namespaces)

    return all_namespaces