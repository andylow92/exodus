# Exodus

```
███████╗██╗  ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔═══██╗██╔══██╗██║   ██║██╔════╝
█████╗   ╚███╔╝ ██║   ██║██║  ██║██║   ██║███████╗
██╔══╝   ██╔██╗ ██║   ██║██║  ██║██║   ██║╚════██║
███████╗██╔╝ ██╗╚██████╔╝██████╔╝╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝
```
Exodus is an open-source Python project designed to help developers smoothly migrate secrets between HashiCorp Vault clusters. In particular, it focuses on copying secrets from a KV (Key-Value) v1 or v2 mount in one Vault instance to another Vault instance.

    Disclaimer: This is not an official HashiCorp-supported tool or code. It was created by me for the community to assist anyone who needs to migrate Vault secrets. Use at your own risk.

Features

    KV v1 or KV v2 support: seamlessly copy secrets from either version.
    Recursive listing of all secrets (subpaths) in the source Vault.
    Preserves paths (with optional root path changes).
    Dry-run mode to list copy operations without actually writing to the destination.
    Rate limiting to avoid overloading your Vault server with requests.
    Vault Enterprise namespaces supported.
    Configurable SSL/TLS verification with optional CA certificates or --skip-verify.

Installation

To install Exodus from PyPI:

pip install vault-exodus

(Or install a specific version: pip install vault-exodus==0.1.1.)
Requirements

    Python 3.7+ (Recommended)
    Requests
    tqdm

If you install via pip install vault-exodus, these dependencies are automatically installed.
Usage (CLI)

Once installed, a CLI command named exodus is available. You can run:

exodus [OPTIONS]

Common Arguments
Argument	Description	Default
--vault-a-addr	URL of the source Vault (Enterprise) instance.	http://localhost:8200
--vault-a-token	Token for the source Vault. (Required)	-
--vault-a-mount	KV mount name in the source Vault.	secret
--vault-a-path-root	Root path (folder) in the source Vault to copy from.	myapp
--vault-a-namespace	Namespace header for the source Vault (if applicable).	(empty)
--vault-a-kv-version	KV version for the source Vault (1 or 2).	2
--vault-b-addr	URL of the destination Vault (HCP) instance.	http://localhost:8200
--vault-b-token	Token for the destination Vault. (Required)	-
--vault-b-mount	KV mount name in the destination Vault.	secret
--vault-b-path-root	Root path (folder) in the destination Vault to copy to.	myapp-copied
--vault-b-namespace	Namespace header for the destination Vault (if applicable).	(empty)
--vault-b-kv-version	KV version for the destination Vault (1 or 2).	2
--rate-limit	Delay in seconds between copying each secret.	0.1
--dry-run	List copy operations without writing secrets to the destination Vault. (flag)	(off)
--vault-a-ca-cert	Path to CA certificate for the source Vault.	(none)
--vault-b-ca-cert	Path to CA certificate for the destination Vault.	(none)
--vault-a-skip-verify	Skip SSL verification for the source Vault. (flag)	(off)
--vault-b-skip-verify	Skip SSL verification for the destination Vault. (flag)	(off)
Example

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

This command:

    Connects to the source Vault at https://source-vault.example.com (KV v2).
    Uses token s.ABCD1234, reading secrets under mount secret/myapp in namespace admin.
    Lists what would be copied to the destination Vault at https://destination-vault.example.com, token s.EFGH5678, mount secret/myapp-copied (KV v2).
    Introduces a 0.5-second delay between each secret copy (or listing, if --dry-run).
    No actual writes occur, because --dry-run is specified.

Usage (Library)

You can also import Exodus’s functions in your own Python scripts:

from exodus.kv_migrator import list_secrets, read_secret, write_secret

def main():
    vault_addr = "http://localhost:8200"
    token = "my-vault-token"
    mount = "secret"
    path = "myapp"

    # 1. List secrets
    secret_paths = list_secrets(
        vault_addr=vault_addr,
        token=token,
        mount=mount,
        path=path,
        kv_version="2"  # or "1"
    )
    print("Discovered paths:", secret_paths)

    # 2. Read a specific secret
    if secret_paths:
        first_secret = read_secret(
            vault_addr=vault_addr,
            token=token,
            mount=mount,
            path=secret_paths[0],
            kv_version="2"
        )
        print("First secret data:", first_secret)

    # 3. Write a secret (to the same or another Vault)
    write_secret(
        vault_addr="http://another-vault:8200",
        token="another-token",
        mount="secret",
        path="myapp-copied/secret1",
        secret_data=first_secret,
        kv_version="2"
    )

if __name__ == "__main__":
    main()

(Remember to install vault-exodus first, e.g., pip install vault-exodus in a virtual environment.)
How It Works

    Check & Validate
        Ensures the mounts you specify are accessible and that your tokens have the necessary read/write permissions (particularly for KV v2 if you try to do those operations).

    List Secrets
        Recursively collects all secret paths from the --vault-a-path-root.

    Copy Secrets
        Reads secrets from the source, writes them to the corresponding path in the destination.
        Dry-run mode logs the operation instead of writing.

    Rate Limiting
        The --rate-limit flag introduces a delay (in seconds) between each secret copy to avoid performance issues or rate-limiting.

Notes & Recommendations

    Always test in a non-production environment or with --dry-run to confirm the behavior before performing real migrations.
    Large datasets or many secrets? Increase --rate-limit to reduce load on your Vault servers.
    Use valid CA certificates or --skip-verify carefully in secure environments.
    Confirm your tokens have the appropriate policies (read on source, write on destination).

Contributing

Contributions, suggestions, and issue reports are welcome! Feel free to open a pull request or file an issue on GitHub if you’d like to improve this project.
License

This project is distributed under the MIT License. See the LICENSE file for details.

Again, note: This is not an official HashiCorp tool. It is a community-driven script created to help anyone needing to migrate secrets between Vault instances. Always confirm it meets your security and compliance requirements before use. Use it at your own risk.