# SPDX-License-Identifier: MIT

import json
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPLORER_JS = REPO_ROOT / "explorer" / "static" / "js" / "explorer.js"


def run_node(script):
    return subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def test_explorer_normalizes_paginated_miners_payload():
    script = textwrap.dedent(
        f"""
        const fs = require('fs');
        const vm = require('vm');

        const sandbox = {{
          console,
          setTimeout,
          clearTimeout,
          setInterval: () => 0,
          fetch: async () => {{ throw new Error('fetch should not run'); }},
          window: {{ EXPLORER_API_BASE: 'https://node.example' }},
          document: {{
            addEventListener: () => {{}},
            querySelectorAll: () => [],
            getElementById: () => null
          }}
        }};
        sandbox.window.window = sandbox.window;
        sandbox.window.document = sandbox.document;

        vm.createContext(sandbox);
        vm.runInContext(fs.readFileSync({json.dumps(str(EXPLORER_JS))}, 'utf8'), sandbox);

        const normalize = sandbox.window.RustChainExplorer.normalizeMinersPayload;
        const rows = normalize({{
          miners: [
            {{
              miner: 'power8-s824-sophia',
              device_arch: 'POWER8',
              antiquity_multiplier: 2,
              last_attest: 1779059287
            }},
            {{
              miner_id: 'legacy-miner',
              device_arch: 'x86_64',
              multiplier: 1.25,
              last_seen: 1779059000
            }}
          ],
          pagination: {{ total: 2, limit: 20, offset: 0 }}
        }});

        console.log(JSON.stringify({{
          paginatedCount: rows.length,
          firstMiner: rows[0].miner_id,
          firstMultiplier: rows[0].multiplier,
          firstLastSeen: rows[0].last_seen,
          secondMiner: rows[1].miner_id,
          arrayCount: normalize([{{ miner_id: 'direct' }}]).length,
          invalidCount: normalize({{ pagination: {{ total: 0 }} }}).length
        }}));
        """
    )

    result = json.loads(run_node(script))

    assert result == {
        "paginatedCount": 2,
        "firstMiner": "power8-s824-sophia",
        "firstMultiplier": 2,
        "firstLastSeen": 1779059287,
        "secondMiner": "legacy-miner",
        "arrayCount": 1,
        "invalidCount": 0,
    }
