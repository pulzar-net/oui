// The lookup both consoles use, as a reference: at most two small fetches per
// MAC, cached per file, and nothing fetched for a private address.
//
//   const vendor = await lookup('3c:5a:37:12:34:56', fetchJson)
//
// `fetchJson(path)` returns the parsed file at BASE + path, or null on 404.

export const BASE = 'https://oss.pulzr.net/oui/';

/** The MAC as 12 uppercase hex digits, or null. */
export function hex(mac) {
  const h = String(mac || '').replace(/[^0-9a-fA-F]/g, '').toUpperCase();
  return h.length === 12 ? h : null;
}

/** A locally administered address (phones and laptops randomize theirs) has
 * no vendor to find. */
export function isPrivate(h) {
  return (parseInt(h.slice(0, 2), 16) & 0x02) !== 0;
}

export async function lookup(mac, fetchJson) {
  const h = hex(mac);
  if (!h) return null;
  if (isPrivate(h)) return { private: true };
  const shard = await fetchJson(`v1/${h.slice(0, 4)}.json`);
  if (!shard) return null;
  if (shard.split && shard.split.includes(h.slice(0, 6))) {
    const slice = await fetchJson(`v1/${h.slice(0, 7)}.json`);
    const name = slice && slice.prefixes[h.slice(0, 9)];
    if (name) return { name, prefix: h.slice(0, 9) };
  }
  for (const n of [7, 6]) {
    const name = shard.prefixes[h.slice(0, n)];
    if (name) return { name, prefix: h.slice(0, n) };
  }
  return null;
}
