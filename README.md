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

```python
from exodus.kv_migrator import list_secrets, read_secret, write_secret

def main():
    vault_addr = "http://localhost:8200"
    token = "my-vault-token"
    mount = "secret"
    path = "myapp"

    # List secrets
    secret_paths = list_secrets(
        vault_addr=vault_addr,
        token=token,
        mount=mount,
        path=path,
        kv_version="2"
    )

    # Read and write secrets
    if secret_paths:
        secret = read_secret(
            vault_addr=vault_addr,
            token=token,
            mount=mount,
            path=secret_paths[0],
            kv_version="2"
        )
        
        write_secret(
            vault_addr="http://another-vault:8200",
            token="another-token",
            mount="secret",
            path="myapp-copied/secret1",
            secret_data=secret,
            kv_version="2"
        )

if __name__ == "__main__":
    main()
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