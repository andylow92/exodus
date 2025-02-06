# Exodus

```
███████╗██╗  ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔═══██╗██╔══██╗██║   ██║██╔════╝
█████╗   ╚███╔╝ ██║   ██║██║  ██║██║   ██║███████╗
██╔══╝   ██╔██╗ ██║   ██║██║  ██║██║   ██║╚════██║
███████╗██╔╝ ██╗╚██████╔╝██████╔╝╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝
```
# Exodus

A Python tool for migrating secrets between HashiCorp Vault clusters. Supports copying secrets from KV v1/v2 mounts between Vault instances.

> **Disclaimer**: This is not an official HashiCorp tool. Community-created project for Vault secrets migration. Use at your own risk.

## Features

- KV v1 and v2 mount support
- Recursive secret listing with subpath preservation
- Optional root path modifications
- Dry-run mode for operation preview
- Configurable rate limiting
- Vault Enterprise namespace support
- Flexible SSL/TLS verification with CA certificates

## Installation

```bash
pip install vault-exodus  # Latest version
pip install vault-exodus==0.1.1  # Specific version
```

### Requirements
- Python 3.7+ (Recommended)
- Requests
- tqdm

Dependencies are automatically installed via pip.

## Usage

### CLI

```bash
exodus [OPTIONS]
```

#### Key Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--vault-a-addr` | Source Vault URL | http://localhost:8200 |
| `--vault-a-token` | Source Vault token | Required |
| `--vault-a-mount` | Source KV mount name | secret |
| `--vault-a-path-root` | Source root path | myapp |
| `--vault-b-addr` | Destination Vault URL | http://localhost:8200 |
| `--vault-b-token` | Destination Vault token | Required |
| `--vault-b-mount` | Destination KV mount name | secret |
| `--vault-b-path-root` | Destination root path | myapp-copied |

[View complete arguments table in documentation]

### Example

```bash
exodus \
  --vault-a-addr="https://source-vault.example.com" \
  --vault-a-token="s.ABCD1234" \
  --vault-a-mount="secret" \
  --vault-a-path-root="myapp" \
  --vault-a-namespace="admin" \
  --vault-a-kv-version="2" \
  --vault-b-addr="https://destination-vault.example.com" \
  --vault-b-token="s.EFGH5678" \
  --vault-b-mount="secret" \
  --vault-b-path-root="myapp-copied" \
  --vault-b-kv-version="2" \
  --rate-limit=0.5 \
  --dry-run
```

### Python Library Usage

## kv secrets engine 

```python
from exodus.kv_migrator import list_secrets, read_secret, write_secret
from tqdm import tqdm
import time
import logging

logging.basicConfig(
   level=logging.INFO,
   format="%(asctime)s [%(levelname)s] %(message)s"
)

def simple_migrate(
   src_addr, src_token, src_mount, src_root, src_kv_version, src_namespace,
   dst_addr, dst_token, dst_mount, dst_root, dst_kv_version, dst_namespace,
   dry_run=False, rate_limit=1.0
):
   logging.info(f"Listing secrets in '{src_root}' from {src_addr} (KV v{src_kv_version})")
   
   secret_paths = list_secrets(
       vault_addr=src_addr,
       token=src_token,
       mount=src_mount,
       path=src_root,
       kv_version=src_kv_version,
       namespace=src_namespace,
       verify=False
   )

   logging.info(f"Found {len(secret_paths)} secrets to copy")
   failed_copies = []
   
   for spath in tqdm(secret_paths, desc="Copying secrets"):
       try:
           data = read_secret(
               vault_addr=src_addr,
               token=src_token,
               mount=src_mount,
               path=spath,
               kv_version=src_kv_version,
               namespace=src_namespace,
               verify=False
           )
           if not data:
               logging.debug(f"No data for '{spath}'; skipping")
               continue
               
           if spath.startswith(src_root + "/"):
               relative = spath[len(src_root)+1:]
               dpath = f"{dst_root}/{relative}"
           else:
               dpath = f"{dst_root}/{spath}"
               
           if dry_run:
               logging.info(f"[Dry Run] Would copy '{spath}' -> '{dpath}'")
           else:
               write_secret(
                   vault_addr=dst_addr,
                   token=dst_token,
                   mount=dst_mount,
                   path=dpath,
                   secret_data=data,
                   kv_version=dst_kv_version,
                   namespace=dst_namespace,
                   verify=False
               )
               logging.info(f"Copied '{spath}' -> '{dpath}'")
           
           if rate_limit > 0:
               time.sleep(rate_limit)
               
       except Exception as e:
           failed_copies.append((spath, str(e)))
           logging.error(f"Failed to copy '{spath}': {e}")

   if failed_copies:
       logging.error("\nSome secrets failed to copy:")
       for path, error in failed_copies:
           logging.error(f" - {path}: {error}")

def main():
   # Example usage
   simple_migrate(
       src_addr="http://localhost:8200",
       src_token="root",
       src_mount="secret", 
       src_root="myapp",
       src_kv_version="2",
       src_namespace="admin",
       dst_addr="http://localhost:8200",
       dst_token="root",
       dst_mount="secret",
       dst_root="myapp-copied",
       dst_kv_version="2",
       dst_namespace="admin",
       dry_run=True
   )

if __name__ == "__main__":
   main()
```

## list namespaces 
depth control works the following way:

max_depth=1: Only direct children
max_depth=2: Children and grandchildren
max_depth=0: All levels (unlimited)
```python
import os
import logging
from exodus.namespace import list_namespaces

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_namespace_depths():
    # Get environment variables
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN")
    base_namespace = os.getenv("VAULT_NAMESPACE", "admin")
    max_depth = int(os.getenv("VAULT_MAX_DEPTH", "1"))
    
    if not vault_token:
        raise ValueError("VAULT_TOKEN environment variable must be set")

    print(f"Testing with:")
    print(f"Base namespace: '{base_namespace}'")
    print(f"Max depth: {max_depth}")

    # Call the library function
    namespaces = list_namespaces(
        vault_addr=vault_addr,
        token=vault_token,
        base_namespace=base_namespace,
        max_depth=max_depth
    )

    print("\n=== Namespaces Found ===")
    if not namespaces:
        print("No namespaces found.")
    else:
        for ns in sorted(namespaces):
            depth = len(ns.split('/')) - 1
            indent = "  " * depth
            print(f"{indent}- {ns}")

if __name__ == "__main__":
    test_namespace_depths()
  ```

Remember to
 ```bash
# First set your environment variables if not already set
export VAULT_ADDR="your-vault-address"
export VAULT_TOKEN="your-token"
export VAULT_NAMESPACE="admin"
export VAULT_MAX_DEPTH=1

 ```
## list auth methods and secret engines  
```python
import os
import logging
from typing import Dict, Any
from exodus.auth import list_auth_methods
from exodus.secret import list_secret_engines

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def test_vault_backends(
    vault_addr: str,
    token: str,
    namespace: str = "",
    verify: bool = True
) -> Dict[str, Dict[str, Any]]:
    """
    Test function to list both auth methods and secret engines.
    
    Args:
        vault_addr: Vault server address
        token: Vault token
        namespace: Namespace to inspect
        verify: SSL verification
    """
    results = {
        'auth_methods': {},
        'secret_engines': {}
    }

    try:
        # List auth methods
        auth_methods = list_auth_methods(
            vault_addr=vault_addr,
            token=token,
            namespace=namespace,
            verify=verify
        )
        results['auth_methods'] = auth_methods

        # List secret engines
        secret_engines = list_secret_engines(
            vault_addr=vault_addr,
            token=token,
            namespace=namespace,
            verify=verify
        )
        results['secret_engines'] = secret_engines

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")

    return results

def main():
    # Get environment variables
    VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
    VAULT_TOKEN = os.getenv("VAULT_TOKEN")
    BASE_NAMESPACE = os.getenv("VAULT_NAMESPACE", "admin")
    SKIP_VERIFY = os.getenv("VAULT_SKIP_VERIFY", "false").lower() == "true"

    # Validate required environment variables
    if not VAULT_TOKEN:
        raise ValueError("VAULT_TOKEN environment variable must be set")

    # Log configuration
    logging.info(f"Vault address: {VAULT_ADDR}")
    logging.info(f"Base namespace: '{BASE_NAMESPACE}' (empty means root)")
    logging.info(f"SSL verification: {'disabled' if SKIP_VERIFY else 'enabled'}")

    try:
        results = test_vault_backends(
            vault_addr=VAULT_ADDR,
            token=VAULT_TOKEN,
            namespace=BASE_NAMESPACE,
            verify=not SKIP_VERIFY
        )

        # Print auth methods
        print("\n=== Enabled Auth Methods ===")
        if not results['auth_methods']:
            print(" No auth methods found")
        else:
            for path, config in sorted(results['auth_methods'].items()):
                print(f" - {path}: {config['type']}")
                # Optionally print more details
                if 'description' in config:
                    print(f"   Description: {config['description']}")

        # Print secret engines
        print("\n=== Enabled Secret Engines ===")
        if not results['secret_engines']:
            print(" No secret engines found")
        else:
            for path, config in sorted(results['secret_engines'].items()):
                print(f" - {path}: {config['type']}")
                # Optionally print more details
                if 'description' in config:
                    print(f"   Description: {config['description']}")

    except Exception as e:
        logging.error(f"Failed to list backends: {str(e)}")
        raise

if __name__ == "__main__":
    main()
  ```
```
export VAULT_ADDR="https://vault.example.com:8200"
export VAULT_TOKEN="your-token"
export VAULT_NAMESPACE="admin"
export VAULT_SKIP_VERIFY="true"  # Optional for testing
  ```

## Best Practices

- Test migrations with `--dry-run` before production use
- Increase `--rate-limit` for large datasets
- Use appropriate CA certificates in secure environments
- Verify token permissions (read on source, write on destination)

## Contributing

Contributions welcome! Please feel free to submit pull requests or issues on GitHub.

## License

MIT License. See [LICENSE](LICENSE) file for details.

Again, note: This is not an official HashiCorp tool. It is a community-driven script created to help anyone needing to migrate secrets between Vault instances. Always confirm it meets your security and compliance requirements before use. Use it at your own risk.
