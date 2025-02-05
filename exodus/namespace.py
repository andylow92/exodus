# /exodus/exodus/namespace.py  

import logging
from typing import List, Optional
import requests

def list_namespaces(
    vault_addr: str,
    token: str,
    base_namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None,
    suppress_404: bool = True
) -> List[str]:
    """
    Recursively list all child namespaces under the specified base_namespace.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        base_namespace: Starting namespace
        verify: SSL verification
        session: Optional requests session
        suppress_404: If True, suppresses warnings for 404 errors (empty namespaces)
    """
    if session is None:
        session = requests.Session()

    headers = {"X-Vault-Token": token}
    if base_namespace:
        headers["X-Vault-Namespace"] = base_namespace

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
    elif resp.status_code == 404:
        if not suppress_404:
            logging.debug(f"No child namespaces found under '{base_namespace}'")
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

        child_namespaces = list_namespaces(
            vault_addr=vault_addr,
            token=token,
            base_namespace=new_namespace,
            verify=verify,
            session=session,
            suppress_404=suppress_404
        )
        all_namespaces.extend(child_namespaces)

    return all_namespaces