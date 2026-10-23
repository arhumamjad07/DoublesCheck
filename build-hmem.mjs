// Build pinned upstream TypeScript without downloading compiler dependencies.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { stripTypeScriptTypes } from 'node:module';
const root = path.dirname(fileURLToPath(import.meta.url));
const vendor = path.join(root, 'vendor', 'hmem');
const output = path.join(vendor, 'compiled');
for (const folder of ['reference/src', 'conformance']) {
  for (const entry of fs.readdirSync(path.join(vendor, folder), {withFileTypes: true})) {
    if (!entry.isFile() || !entry.name.endsWith('.ts')) continue;
    const relative = path.join(folder, entry.name);
    const source = fs.readFileSync(path.join(vendor, relative), 'utf8');
    const generated = stripTypeScriptTypes(source, {mode: 'transform'})
      .replaceAll('.ts"', '.mjs"').replaceAll(".ts'", ".mjs'");
    const destination = path.join(output, relative.replace(/\.ts$/, '.mjs'));
    fs.mkdirSync(path.dirname(destination), {recursive: true});
    fs.writeFileSync(destination, '// Generated from pinned Meterless H-MEM source; see UPSTREAM.json.\n' + generated);
  }
}
fs.cpSync(path.join(vendor, 'conformance', 'vectors'), path.join(output, 'conformance', 'vectors'), {recursive: true});
console.log('Built H-MEM engine and official conformance runner.');
