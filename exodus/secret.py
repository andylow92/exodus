#!/usr/bin/env python3
import logging
from typing import List, Dict, Any, Optional
import requests

def list_secret_engines(
    vault_addr: str,
    token: str,
    namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    List secret engines enabled in Vault.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        namespace: Optional namespace
        verify: SSL verification
        session: Optional requests session
    
    Returns:
        Dictionary of enabled secret engines and their configurations
    """
    if session is None:
        session = requests.Session()

    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace

    url = f"{vault_addr}/v1/sys/mounts"

    try:
        resp = session.get(url, headers=headers, verify=verify)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        else:
            logging.warning(
                f"Error listing secret engines: "
                f"HTTP {resp.status_code} - {resp.text}"
            )
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
    except ValueError as e:
        logging.error(f"Invalid JSON response: {str(e)}")

    return {}

def get_secret_engine_config(
    vault_addr: str,
    token: str,
    path: str,
    namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    Get configuration for a specific secret engine.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        path: Path where the secret engine is mounted
        namespace: Optional namespace
        verify: SSL verification
        session: Optional requests session
    """
    if session is None:
        session = requests.Session()

    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace

    url = f"{vault_addr}/v1/sys/mounts/{path}/tune"

    try:
        resp = session.get(url, headers=headers, verify=verify)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        else:
            logging.warning(
                f"Error getting secret engine config for {path}: "
                f"HTTP {resp.status_code} - {resp.text}"
            )
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
    except ValueError as e:
        logging.error(f"Invalid JSON response: {str(e)}")

    return {}