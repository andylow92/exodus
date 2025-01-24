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
#!/usr/bin/env python3
from exodus.kv_migrator import list_secrets, read_secret, write_secret

def simple_migrate(
   src_addr, src_token, src_mount, src_root, src_kv_version, src_namespace="",
   dst_addr, dst_token, dst_mount, dst_root, dst_kv_version, dst_namespace="",
   dry_run=False
):
   secret_paths = list_secrets(
       vault_addr=src_addr,
       token=src_token,
       mount=src_mount,
       path=src_root,
       kv_version=src_kv_version,
       namespace=src_namespace,
       verify=False
   )
   for spath in secret_paths:
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
           continue
           
       if spath.startswith(src_root + "/"):
           relative = spath[len(src_root)+1:]
           dpath = f"{dst_root}/{relative}"
       else:
           dpath = f"{dst_root}/{spath}"
           
       if dry_run:
           print(f"[Dry Run] {spath} -> {dpath}")
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
           print(f"Copied {spath} -> {dpath}")

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