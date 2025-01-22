# Exodus

```
███████╗██╗  ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗
██╔════╝╚██╗██╔╝██╔═══██╗██╔══██╗██║   ██║██╔════╝
█████╗   ╚███╔╝ ██║   ██║██║  ██║██║   ██║███████╗
██╔══╝   ██╔██╗ ██║   ██║██║  ██║██║   ██║╚════██║
███████╗██╔╝ ██╗╚██████╔╝██████╔╝╚██████╔╝███████║
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝
```

Exodus is an open-source Python project designed to help developers smoothly migrate secrets between HashiCorp Vault clusters. In particular, it focuses on copying secrets from a KV (Key-Value) v2 mount in one Vault instance to another Vault instance.

    Disclaimer: This is not an official HashiCorp-supported tool or code. It was created by me for the community to assist anyone who needs to migrate Vault secrets. Use at your own discretion.

Features

    Recursively lists all KV v2 secrets in the source Vault.
    Copies secrets to the destination Vault, preserving paths (with optional root path changes).
    Supports dry-run mode to verify paths and secrets without actually writing to the destination.
    Rate-limiting to avoid overloading the system with requests.
    Support for Vault Enterprise namespaces.
    Configurable SSL/TLS verification, including CA certificates.

Requirements

    Python 3.7+ (Recommended)
    Requests
    tqdm

You can install the dependencies with:

pip install requests tqdm

Usage

python exodus.py [OPTIONS]

Common Arguments
Argument	Description	Default
--vault-a-addr	URL of the source Vault (Enterprise) instance.	http://localhost:8200
--vault-a-token	Token for the source Vault. (Required)	-
--vault-a-mount	KV v2 mount name in the source Vault.	secret
--vault-a-path-root	Root path (folder) in the source Vault to copy from.	myapp
--vault-a-namespace	Namespace header for the source Vault (if applicable).	(empty)
--vault-b-addr	URL of the destination Vault (HCP) instance.	http://localhost:8200
--vault-b-token	Token for the destination Vault. (Required)	-
--vault-b-mount	KV v2 mount name in the destination Vault.	secret
--vault-b-path-root	Root path (folder) in the destination Vault to copy to.	myapp-copied
--vault-b-namespace	Namespace header for the destination Vault (if applicable).	(empty)
--rate-limit	Delay in seconds between copying each secret.	0.1
--dry-run	If set, only lists what would be copied without actually writing secrets to Vault B.	(flag)
--vault-a-ca-cert	Path to the CA certificate for the source Vault.	(none)
--vault-b-ca-cert	Path to the CA certificate for the destination Vault.	(none)
--vault-a-skip-verify	Skip SSL certificate verification for the source Vault.	(flag)
--vault-b-skip-verify	Skip SSL certificate verification for the destination Vault.	(flag)
Example

python exodus.py \
  --vault-a-addr="https://source-vault.example.com" \
  --vault-a-token="s.ABCD1234" \
  --vault-a-mount="secret" \
  --vault-a-path-root="myapp" \
  --vault-a-namespace="admin" \
  --vault-b-addr="https://destination-vault.example.com" \
  --vault-b-token="s.EFGH5678" \
  --vault-b-mount="secret" \
  --vault-b-path-root="myapp-copied" \
  --rate-limit=0.5 \
  --dry-run

This command:

    Connects to the source Vault at https://source-vault.example.com.
    Uses token s.ABCD1234.
    Reads secrets from KV v2 mount secret, under the path myapp, within namespace admin.
    Lists what would be copied to the destination Vault at https://destination-vault.example.com using token s.EFGH5678.
    It would write secrets to KV v2 mount secret, under the path myapp-copied.
    Introduces a 0.5-second delay between each secret copy (or listing, if dry-run).
    Since --dry-run is specified, no actual writes occur.

How It Works

    Check and Validate
        Verifies both source and destination Vault mounts are KV v2.
        Confirms that the provided token has the necessary permissions (read or root) to access the source Vault mount.

    List Secrets
        Recursively gathers all secret paths from the specified --vault-a-path-root.

    Copy Secrets
        For each secret path found, reads the data from the source Vault.
        Writes that data to the corresponding path on the destination Vault.
        If --dry-run is used, it only logs what would be done, without performing the actual write.

    Rate Limiting
        Uses the specified --rate-limit (in seconds) to control how quickly secrets are copied.

Notes and Recommendations

    Always test in a non-production environment or with --dry-run first to verify that everything behaves as expected.
    If you have many secrets or a large data size, consider adjusting the rate limit to avoid rate-limiting or performance issues on your Vault servers.
    Use appropriate CA certificates or enable/disable verification as needed for secure communication with Vault instances.

Contributing

Contributions, suggestions, and issue reports are welcome! Feel free to submit a pull request or file an issue in this repository.
License

This project is distributed under the MIT License. See the LICENSE file for details.

Again, please note: This is not an official HashiCorp tool. It is a community-driven script created to help anyone needing to migrate secrets between Vault instances. Use it responsibly and always confirm it meets your security and compliance requirements before use.
