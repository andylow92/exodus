#!/usr/bin/env python3

import sys
import time
import argparse
import logging
from tqdm import tqdm

from exodus.kv_migrator import (
    list_secrets,
    read_secret,
    write_secret,
    get_verify_param
)

# ----------------------------
# Default Settings
# ----------------------------
DEFAULT_VAULT_A_ADDR = "http://localhost:8200"
DEFAULT_VAULT_B_ADDR = "http://localhost:8200"
DEFAULT_KV_MOUNT = "secret"
DEFAULT_PATH_ROOT = "myapp"
DEFAULT_PATH_ROOT_DEST = "myapp-copied"
DEFAULT_RATE_LIMIT = 0.1

# Logging Setup
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy KV (v1 or v2) secrets between two Vault instances."
    )

    # Vault A (source) config
    parser.add_argument("--vault-a-addr", default=DEFAULT_VAULT_A_ADDR,
                        help="URL of the source Vault (Enterprise) instance.")
    parser.add_argument("--vault-a-token", required=True,
                        help="Token for the source Vault.")
    parser.add_argument("--vault-a-mount", default=DEFAULT_KV_MOUNT,
                        help="KV mount name in source Vault (default: secret).")
    parser.add_argument("--vault-a-path-root", default=DEFAULT_PATH_ROOT,
                        help="Root path (folder) in source Vault to copy from (default: myapp).")
    parser.add_argument("--vault-a-namespace", default="",
                        help="Namespace header for source Vault (if applicable).")
    parser.add_argument("--vault-a-kv-version", choices=["1", "2"], default="2",
                        help="KV version used by the source Vault mount (1 or 2). Default: 2")

    # Vault B (destination) config
    parser.add_argument("--vault-b-addr", default=DEFAULT_VAULT_B_ADDR,
                        help="URL of the destination Vault (HCP) instance.")
    parser.add_argument("--vault-b-token", required=True,
                        help="Token for the destination Vault.")
    parser.add_argument("--vault-b-mount", default=DEFAULT_KV_MOUNT,
                        help="KV mount name in destination Vault (default: secret).")
    parser.add_argument("--vault-b-path-root", default=DEFAULT_PATH_ROOT_DEST,
                        help="Root path (folder) in destination Vault to copy to (default: myapp-copied).")
    parser.add_argument("--vault-b-namespace", default="",
                        help="Namespace header for destination Vault (if applicable).")
    parser.add_argument("--vault-b-kv-version", choices=["1", "2"], default="2",
                        help="KV version used by the destination Vault mount (1 or 2). Default: 2")

    # Additional options
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT,
                        help="Delay in seconds between copying each secret (default: 0.1).")
    parser.add_argument("--dry-run", action="store_true",
                        help="If set, only lists copy operations without writing secrets to Vault B.")

    # SSL/TLS options
    parser.add_argument("--vault-a-ca-cert",
                        help="Path to CA certificate for source Vault")
    parser.add_argument("--vault-b-ca-cert",
                        help="Path to CA certificate for destination Vault")
    parser.add_argument("--vault-a-skip-verify", action="store_true",
                        help="Skip SSL verification for source Vault")
    parser.add_argument("--vault-b-skip-verify", action="store_true",
                        help="Skip SSL verification for destination Vault")

    return parser.parse_args()

def copy_secrets(args):
    """
    1. List all secrets in Vault A.
    2. Read each secret, write to Vault B.
    3. Optional rate limiting.
    4. Dry-run mode support.
    5. Progress bar with tqdm.
    """
    # Determine SSL verify parameters
    vault_a_verify = get_verify_param(
        ca_cert=args.vault_a_ca_cert,
        skip_verify=args.vault_a_skip_verify
    )
    vault_b_verify = get_verify_param(
        ca_cert=args.vault_b_ca_cert,
        skip_verify=args.vault_b_skip_verify
    )

    # 1. List all secrets from Vault A
    logging.info(f"Listing secrets in '{args.vault_a_path_root}' "
                 f"from {args.vault_a_addr} (KV v{args.vault_a_kv_version})")

    secret_paths = list_secrets(
        vault_addr=args.vault_a_addr,
        token=args.vault_a_token,
        mount=args.vault_a_mount,
        path=args.vault_a_path_root,
        namespace=args.vault_a_namespace,
        verify=vault_a_verify,
        kv_version=args.vault_a_kv_version
    )

    logging.info(f"Found {len(secret_paths)} secrets to copy.\n")
    failed_copies = []

    # 2. Copy each secret using tqdm for a progress bar
    for source_path in tqdm(secret_paths, desc="Copying secrets"):
        try:
            # Read from Vault A
            secret_data = read_secret(
                vault_addr=args.vault_a_addr,
                token=args.vault_a_token,
                mount=args.vault_a_mount,
                path=source_path,
                namespace=args.vault_a_namespace,
                verify=vault_a_verify,
                kv_version=args.vault_a_kv_version
            )

            if not secret_data:
                logging.debug(f"No data for '{source_path}'; skipping.")
                continue

            # Construct the destination path
            if args.vault_a_path_root:
                if source_path.startswith(args.vault_a_path_root + '/'):
                    relative_path = source_path[len(args.vault_a_path_root)+1:]
                    destination_path = f"{args.vault_b_path_root}/{relative_path}".strip('/')
                else:
                    destination_path = f"{args.vault_b_path_root}/{source_path}".strip('/')
            else:
                destination_path = f"{args.vault_b_path_root}/{source_path}".strip('/')

            # Dry-run mode
            if args.dry_run:
                logging.info(f"[Dry-Run] Would copy '{source_path}' -> '{destination_path}'")
            else:
                # Write to Vault B
                write_secret(
                    vault_addr=args.vault_b_addr,
                    token=args.vault_b_token,
                    mount=args.vault_b_mount,
                    path=destination_path,
                    secret_data=secret_data,
                    namespace=args.vault_b_namespace,
                    verify=vault_b_verify,
                    kv_version=args.vault_b_kv_version
                )
                logging.info(f"Copied '{source_path}' -> '{destination_path}'")

        except Exception as e:
            failed_copies.append((source_path, str(e)))
            logging.error(f"Failed to copy '{source_path}': {e}")

        # 3. Rate limiting
        if args.rate_limit > 0 and not args.dry_run:
            time.sleep(args.rate_limit)

    # Summarize failures
    if failed_copies:
        logging.error("\nSome secrets failed to copy:")
        for path, error in failed_copies:
            logging.error(f" - {path}: {error}")

def main():
    args = parse_args()

    if not args.vault_a_token or not args.vault_b_token:
        logging.error("Vault tokens for A or B are missing. Exiting.")
        sys.exit(1)

    try:
        copy_secrets(args)
        logging.info("Completed copying secrets from Vault A to Vault B.")
    except Exception as e:
        logging.error(f"Fatal Error: {e}")
        sys.exit(1)

# If someone runs "python -m exodus.cli", or just "exodus" if installed
if __name__ == "__main__":
    main()
