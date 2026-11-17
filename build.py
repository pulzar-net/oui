#!/usr/bin/env python3
"""The IEEE's MAC address registries as small static files, one per first byte.

    python build.py out/

Reads the three public registries (MA-L 24-bit, MA-M 28-bit, MA-S 36-bit
prefixes) and writes small files a client fetches one or two of per MAC, so it
never holds the whole list and only the MAC's first digits leave it:

  v1/<first 4 hex>.json   {"v": 1, "prefixes": {6- or 7-digit prefix: name},
                           "split": [24-bit bases with 36-bit assignments]}
  v1/<first 7 hex>.json   {"v": 1, "prefixes": {9-digit prefix: name}}, only
                           for a split base: one 7th digit's slice of it

A lookup takes v1/<mac[:4]>.json; when mac[:6] is in its `split`, also
v1/<mac[:7]>.json; the longest of mac[:9], mac[:7], mac[:6] found wins. A 404
means no organization holds those digits. Why two levels: one file per first
byte put 430 KB behind 00, and the IEEE's MA-S bases hold thousands of entries
each, so a flat shard of any width leaves some file large.

Standard library only, so the weekly Action needs no installs.
"""

import csv
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

REGISTRIES = {
    'MA-L': 'https://standards-oui.ieee.org/oui/oui.csv',
    'MA-M': 'https://standards-oui.ieee.org/oui28/mam.csv',
    'MA-S': 'https://standards-oui.ieee.org/oui36/oui36.csv',
}
# The IEEE's server refuses some default client names.
AGENT = 'pulzr-oui/1 (+https://github.com/pulzar-net/oui)'
# A registry that comes back this much smaller than it was is a bad download,
# not the world's vendors leaving: keep the files already published.
MIN_ROWS = {'MA-L': 30000, 'MA-M': 4000, 'MA-S': 4000}


def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            if attempt == 3:
                raise
            time.sleep(10 * (attempt + 1))


def rows(name, text):
    """(prefix hex, organization) from one registry. MA-M and MA-S list the
    full 24-bit base in Assignment and the extra digits in the same column."""
    out = []
    for row in csv.DictReader(io.StringIO(text)):
        prefix = (row.get('Assignment') or '').strip().upper()
        org = ' '.join((row.get('Organization Name') or '').split())
        if prefix and org and all(c in '0123456789ABCDEF' for c in prefix):
            out.append((prefix, org))
    if len(out) < MIN_ROWS[name]:
        raise SystemExit(f'{name}: only {len(out)} rows; refusing to publish')
    return out


def main(dest):
    prefixes = {}
    counts = {}
    for name, url in REGISTRIES.items():
        got = rows(name, fetch(url))
        counts[name] = len(got)
        for prefix, org in got:
            prefixes[prefix] = org
    shards, slices, split = {}, {}, {}
    for prefix, org in prefixes.items():
        if len(prefix) == 9:
            slices.setdefault(prefix[:7], {})[prefix] = org
            split.setdefault(prefix[:4], set()).add(prefix[:6])
        else:
            shards.setdefault(prefix[:4], {})[prefix] = org
    base = os.path.join(dest, 'v1')
    os.makedirs(base, exist_ok=True)

    def write(name, body):
        with open(os.path.join(base, f'{name}.json'), 'w', encoding='utf-8') as f:
            json.dump(body, f, ensure_ascii=False, separators=(',', ':'))

    for key in set(shards) | set(split):
        body = {'v': 1, 'prefixes': dict(sorted(shards.get(key, {}).items()))}
        if key in split:
            body['split'] = sorted(split[key])
        write(key, body)
    for key, entries in slices.items():
        write(key, {'v': 1, 'prefixes': dict(sorted(entries.items()))})
    meta = {'v': 1, 'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'counts': counts, 'files': len(set(shards) | set(split)) + len(slices),
            'source': 'IEEE Registration Authority'}
    with open(os.path.join(base, 'meta.json'), 'w') as f:
        json.dump(meta, f, separators=(',', ':'))
    with open(os.path.join(dest, 'index.html'), 'w') as f:
        f.write('<!doctype html><meta charset="utf-8"><title>OUI</title>'
                '<p>MAC address prefixes from the IEEE registries: '
                '<a href="v1/meta.json">v1/meta.json</a>, <code>v1/&lt;first 4 hex&gt;.json</code>, '
                'and <code>v1/&lt;first 7 hex&gt;.json</code> for a split base. '
                'Source: <a href="https://github.com/pulzar-net/oui">pulzar-net/oui</a>.</p>\n')
    print(json.dumps(meta))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out')
