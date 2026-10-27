// Invoke the pinned official CLI with its header assembled only in process memory.
// The OS command line contains no token. No credential/config file is created.
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

if (process.version !== 'v24.22.1') throw new Error('Pinned isolated Node required');
let cursor = dirname(process.execPath);
let root;
while (cursor !== dirname(cursor)) {
  for (const candidate of [join(cursor, '@modelcontextprotocol/inspector'), join(cursor, 'node_modules/@modelcontextprotocol/inspector')]) {
    if (existsSync(join(candidate, 'package.json'))) { root = candidate; break; }
  }
  if (root) break;
  cursor = dirname(cursor);
}
if (!root || JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')).version !== '2.12.0') {
  throw new Error('Pinned Inspector required');
}
const token = process.env.CASEFLOW_INSPECTOR_TOKEN;
if (!token || !/^[A-Za-z0-9_-]{32,128}$/.test(token)) throw new Error('Read credential required');
const { runCli } = await import(pathToFileURL(join(root, 'clients/cli/build/index.js')).href);
await runCli(['node', 'inspector', '--cli', '--protocol-era', 'legacy', '--format', 'json', '--quiet',
  '--transport', 'http', '--header', `Authorization: Bearer ${token}`, ...process.argv.slice(2)]);
