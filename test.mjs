// node test.mjs <built dir>: lookups against a local build.
import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { lookup } from './lookup.mjs';

const dir = process.argv[2] || 'out';
const fetchJson = async (path) => (existsSync(`${dir}/${path}`) ? JSON.parse(readFileSync(`${dir}/${path}`)) : null);
const any = (file) => Object.entries(JSON.parse(readFileSync(`${dir}/v1/${file}`)).prefixes)[0];

const [l, lname] = Object.entries((await fetchJson('v1/0000.json')).prefixes).find(([p]) => p.length === 6);
assert.equal((await lookup(`${l}123456`, fetchJson)).name, lname, 'a 24-bit prefix');
const big = (await fetchJson(`v1/${'70B3'}.json`));
assert.ok(big.split.includes('70B3D5'), '70B3D5 is a split MA-S base');
const [s, sname] = any('70B3D51.json');
assert.equal((await lookup(`${s}ABC`, fetchJson)).name, sname, 'a 36-bit prefix inside a split base');
assert.deepEqual(await lookup('02:00:00:00:00:01', fetchJson), { private: true }, 'a private address');
assert.equal(await lookup('not a mac', fetchJson), null);
console.log('oui lookup ok');
