#!/usr/bin/env python3
import logging
from typing import List, Dict, Any, Optional
import requests

def list_auth_methods(
    vault_addr: str,
    token: str,
    namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    List authentication methods enabled in Vault.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        namespace: Optional namespace
        verify: SSL verification
        session: Optional requests session
    
    Returns:
        Dictionary of enabled auth methods and their configurations
    """
    if session is None:
        session = requests.Session()

    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace

    url = f"{vault_addr}/v1/sys/auth"

    try:
        resp = session.get(url, headers=headers, verify=verify)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        else:
            logging.warning(
                f"Error listing auth methods: "
                f"HTTP {resp.status_code} - {resp.text}"
            )
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
    except ValueError as e:
        logging.error(f"Invalid JSON response: {str(e)}")

    return {}

def get_auth_method_config(
    vault_addr: str,
    token: str,
    path: str,
    namespace: str = "",
    verify: bool = True,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    Get configuration for a specific auth method.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        path: Path where the auth method is mounted
        namespace: Optional namespace
        verify: SSL verification
        session: Optional requests session
    """
    if session is None:
        session = requests.Session()

    headers = {"X-Vault-Token": token}
    if namespace:
        headers["X-Vault-Namespace"] = namespace

    url = f"{vault_addr}/v1/sys/auth/{path}/tune"

    try:
        resp = session.get(url, headers=headers, verify=verify)
        if resp.status_code == 200:
            return resp.json().get("data", {})
        else:
            logging.warning(
                f"Error getting auth method config for {path}: "
                f"HTTP {resp.status_code} - {resp.text}"
            )
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
    except ValueError as e:
        logging.error(f"Invalid JSON response: {str(e)}")

    return {}

'''
from exodus.auth import list_auth_methods
from exodus.secret import list_secret_engines

# List auth methods
auth_methods = list_auth_methods(
    vault_addr="https://vault:8200",
    token="your-token",
    namespace="admin"
)
print("\nEnabled Auth Methods:")
for path, config in auth_methods.items():
    print(f" - {path}: {config['type']}")

# List secret engines
secret_engines = list_secret_engines(
    vault_addr="https://vault:8200",
    token="your-token",
    namespace="admin"
)
print("\nEnabled Secret Engines:")
for path, config in secret_engines.items():
    print(f" - {path}: {config['type']}")

'''