"""
Bootstrap a self-contained CI e2e run: register a fresh throwaway account,
mint an API key, seed ~/.myracingdata/config.json for the client, and drop
ci_creds.json for the assertion step. No stored secrets — every run brings
its own ephemeral identity.
"""

import json
import os
import secrets
import sys
from pathlib import Path

import requests

API = 'https://myracingdata.com/api/v1'


def main():
    run_id = os.environ.get('GITHUB_RUN_ID', secrets.token_hex(4))
    email = f'ci-e2e+{run_id}@example.com'
    password = secrets.token_urlsafe(18) + 'aA1!'

    r = requests.post(f'{API}/auth/register', timeout=20,
                      json={'name': 'CI Robot Rig', 'email': email, 'password': password, 'role': 'driver'})
    if r.status_code != 201:
        print('register failed:', r.status_code, r.text[:200]); return 1

    r = requests.post(f'{API}/auth/login', json={'email': email, 'password': password}, timeout=20)
    r.raise_for_status()
    access = r.json()['access_token']

    r = requests.post(f'{API}/api-keys', headers={'Authorization': f'Bearer {access}'},
                      json={'key_name': 'CI robot rig'}, timeout=20)
    key = r.json().get('api_key')
    if not key:
        print('key mint failed:', r.status_code, r.text[:200]); return 1

    cfg_dir = Path.home() / '.myracingdata'
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / 'config.json').write_text(json.dumps({
        'api_url': API, 'ws_url': 'wss://myracingdata.com/api/v1/ws',
        'api_key': key, 'update_rate_hz': 60,
    }, indent=2))
    Path('ci_creds.json').write_text(json.dumps({'email': email, 'password': password}))
    print(f'bootstrap OK · account {email} · key {key[:8]}… · config seeded')
    return 0


if __name__ == '__main__':
    sys.exit(main())
