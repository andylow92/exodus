
# exodus/exodus/exodus/kv_migrator.py  
import logging
import requests

# If you want `tqdm` or other modules, import them here, but typically
# that's used in the CLI layer.

def make_headers(token, namespace=None):
    """
    Helper to assemble standard Vault headers with optional namespace.
    """
    headers = {
        "X-Vault-Token": token
    }
    if namespace:
        headers["X-Vault-Namespace"] = namespace
    return headers

def get_verify_param(ca_cert=None, skip_verify=False):
    """
    Helper to determine the 'verify' parameter for the requests library.
    :param ca_cert: Path to a CA certificate, if any
    :param skip_verify: If True, ignore SSL cert verification
    :return: either a boolean (False) or the path to the CA cert
    """
    if ca_cert:
        return ca_cert
    return not skip_verify

def list_secrets(vault_addr, token, mount, path, namespace="", verify=True, kv_version="2"):
    """
    Recursively list all secret paths (leaf nodes) for KV v1 or KV v2.
    """
    headers = make_headers(token, namespace=namespace)
    if kv_version == "2":
        url = f"{vault_addr}/v1/{mount}/metadata/{path}?list=true"
    else:  # kv_version == "1"
        if path:
            url = f"{vault_addr}/v1/{mount}/{path}?list=true"
        else:
            url = f"{vault_addr}/v1/{mount}/?list=true"

    resp = requests.get(url, headers=headers, verify=verify)
    if resp.status_code == 404:
        return []
    if resp.status_code != 200:
        logging.warning(f"[List] Error listing '{path}' for KV v{kv_version}: {resp.text}")
        return []

    try:
        keys = resp.json()["data"]["keys"]
    except KeyError:
        logging.warning(f"[List] Unexpected response format for path '{path}': {resp.text}")
        return []

    all_paths = []
    for key in keys:
        if key.endswith("/"):
            subfolder = f"{path}/{key.strip('/')}".strip("/")
            all_paths.extend(list_secrets(
                vault_addr, token, mount, subfolder,
                namespace=namespace, verify=verify, kv_version=kv_version
            ))
        else:
            full_path = f"{path}/{key}".strip("/")
            all_paths.append(full_path)

    return all_paths

def read_secret(vault_addr, token, mount, path, namespace="", verify=True, kv_version="2"):
    """
    Read a secret at 'path' for KV v1 or KV v2.
    """
    headers = make_headers(token, namespace=namespace)
    if kv_version == "2":
        url = f"{vault_addr}/v1/{mount}/data/{path}"
    else:
        url = f"{vault_addr}/v1/{mount}/{path}"

    resp = requests.get(url, headers=headers, verify=verify)
    if resp.status_code == 200:
        try:
            data = resp.json()
            if kv_version == "2":
                return data["data"]["data"]
            else:
                return data["data"]
        except (KeyError, TypeError):
            logging.warning(f"[Read] Unexpected format for '{path}': {resp.text}")
            return {}
    elif resp.status_code == 404:
        logging.debug(f"[Read] Secret not found at '{path}'")
        return {}
    else:
        logging.warning(f"[Read] Error reading '{path}': {resp.text}")
        return {}

def write_secret(vault_addr, token, mount, path, secret_data,
                 namespace="", verify=True, kv_version="2"):
    """
    Write data to a secret at 'path' for KV v1 or KV v2.
    """
    headers = make_headers(token, namespace=namespace)
    headers["Content-Type"] = "application/json"

    if kv_version == "2":
        url = f"{vault_addr}/v1/{mount}/data/{path}"
        # KV v2 expects a JSON payload: { "data": {...} }
        # If the user already provided that shape, we can re-use it.
        if "data" in secret_data and isinstance(secret_data["data"], dict):
            payload = secret_data
        else:
            payload = {"data": secret_data}
    else:
        # KV v1
        url = f"{vault_addr}/v1/{mount}/{path}"
        # KV v1 expects top-level data
        if "data" in secret_data and isinstance(secret_data["data"], dict):
            payload = secret_data["data"]
        else:
            payload = secret_data

    resp = requests.post(url, json=payload, headers=headers, verify=verify)
    if resp.status_code not in (200, 204):
        logging.warning(f"[Write] Error writing '{path}' (KV v{kv_version}): {resp.text}")
