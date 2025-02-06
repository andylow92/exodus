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
    suppress_404: bool = True,
    max_depth: int = 0,
) -> List[str]:
    """
    Recursively list all child namespaces under the specified base_namespace up to max_depth.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        base_namespace: Starting namespace
        verify: SSL verification
        session: Optional requests session
        suppress_404: If True, suppresses warnings for 404 errors (empty namespaces)
        max_depth: Maximum recursion depth. 0 = unlimited (full recursion).

    Returns:
        A list of namespaces discovered under base_namespace.

    Notes:
        - This function issues a LIST request to /v1/sys/namespaces, 
          gathering any child namespaces returned.
        - If max_depth is non-zero and we exceed it, we stop recursing deeper.
        - We log a warning if more than 100 namespaces are found at any single level.
        - We debug-log when max_depth is reached, if set.
    """
    # Validate max_depth
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    # Create a session if none was provided
    if session is None:
        session = requests.Session()

    def _list_namespaces_recursive(base_namespace: str, current_depth: int) -> List[str]:
        # Check depth before making the request; only proceed if within max_depth
        if max_depth != 0 and current_depth > max_depth:
            logging.debug(
                f"Max depth ({max_depth}) reached at namespace '{base_namespace}'"
            )
            return list()

        # Prepare headers
        headers = {"X-Vault-Token": token}
        if base_namespace:
            headers["X-Vault-Namespace"] = base_namespace

        # This endpoint lists the immediate child namespaces
        url = f"{vault_addr}/v1/sys/namespaces"

        # Make the LIST request
        try:
            resp = session.request(method="LIST", url=url, headers=headers, verify=verify)
        except requests.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return list()

        # Handle response status codes
        if resp.status_code == 404:
            if not suppress_404:
                logging.debug(f"No child namespaces found under '{base_namespace}'")
            return list()
        elif resp.status_code != 200:
            logging.warning(
                f"Error listing namespaces under '{base_namespace}': "
                f"HTTP {resp.status_code} - {resp.text}"
            )
            return list()

        # Safely parse JSON
        try:
            data = resp.json().get("data", {})
            keys = data.get("keys", [])
        except ValueError as e:
            logging.error(f"Invalid JSON response: {str(e)}")
            return list()

        # Optional: Warn when a large number of namespaces is found
        if len(keys) > 100:
            logging.warning(
                f"Large number of namespaces ({len(keys)}) found under '{base_namespace}'"
            )

        all_namespaces: List[str] = []

        # Iterate over each child namespace key
        for key in keys:
            # For each key like "team1/", remove trailing slash -> "team1"
            sub_ns = key.rstrip("/")
            # Construct the new namespace path
            new_namespace = f"{base_namespace}/{sub_ns}" if base_namespace and sub_ns else sub_ns

            # Add the newly found namespace to the list
            all_namespaces.append(new_namespace)

            # Recursively list children of the new namespace (depth + 1)
            child_namespaces = _list_namespaces_recursive(
                base_namespace=new_namespace,
                current_depth=current_depth + 1,
            )
            all_namespaces.extend(child_namespaces)

        return all_namespaces

    # Start the recursion from depth 0
    return _list_namespaces_recursive(base_namespace, 0)