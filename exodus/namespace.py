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
                  Depth is calculated based on namespace structure relative to base_namespace.

    Returns:
        A list of namespaces discovered under base_namespace.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    # Create a session if none was provided
    if session is None:
        session = requests.Session()

    def calculate_relative_depth(namespace: str) -> int:
        """Calculate depth relative to base_namespace."""
        if not namespace:
            return 0
        base_components = len(base_namespace.split('/')) if base_namespace else 0
        namespace_components = len(namespace.split('/'))
        return namespace_components - base_components

    def _list_namespaces_recursive(current_namespace: str) -> List[str]:
        # Check depth before making the request
        current_relative_depth = calculate_relative_depth(current_namespace)
        if max_depth != 0 and current_relative_depth >= max_depth:
            logging.debug(
                f"Max depth ({max_depth}) reached at namespace '{current_namespace}'"
            )
            return []

        # Prepare headers
        headers = {"X-Vault-Token": token}
        if current_namespace:
            headers["X-Vault-Namespace"] = current_namespace

        url = f"{vault_addr}/v1/sys/namespaces"

        # Make the LIST request
        try:
            resp = session.request(method="LIST", url=url, headers=headers, verify=verify)
        except requests.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            return []

        # Handle response status codes
        if resp.status_code == 404:
            if not suppress_404:
                logging.debug(f"No child namespaces found under '{current_namespace}'")
            return []
        elif resp.status_code != 200:
            logging.warning(
                f"Error listing namespaces under '{current_namespace}': "
                f"HTTP {resp.status_code} - {resp.text}"
            )
            return []

        # Safely parse JSON
        try:
            data = resp.json().get("data", {})
            keys = data.get("keys", [])
        except ValueError as e:
            logging.error(f"Invalid JSON response: {str(e)}")
            return []

        # Optional: Warn when a large number of namespaces is found
        if len(keys) > 100:
            logging.warning(
                f"Large number of namespaces ({len(keys)}) found under '{current_namespace}'"
            )

        found_namespaces: List[str] = []

        # Iterate over each child namespace key
        for key in keys:
            # For each key like "team1/", remove trailing slash -> "team1"
            sub_ns = key.rstrip("/")
            # Construct the new namespace path
            new_namespace = f"{current_namespace}/{sub_ns}" if current_namespace and sub_ns else sub_ns

            # Add the newly found namespace to the list
            found_namespaces.append(new_namespace)

            # Only recurse if we haven't reached max_depth
            new_relative_depth = calculate_relative_depth(new_namespace)
            if max_depth == 0 or new_relative_depth < max_depth:
                child_namespaces = _list_namespaces_recursive(new_namespace)
                found_namespaces.extend(child_namespaces)

        return found_namespaces

    return _list_namespaces_recursive(base_namespace)