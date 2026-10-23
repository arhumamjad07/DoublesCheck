const path = require('node:path');
const {spawnSync} = require('node:child_process');
const result = spawnSync(process.execPath,
  [path.join(__dirname,'vendor/hmem/compiled/conformance/runner.mjs')],
  {stdio:'inherit',env:{...process.env,HMEM_IMPL:path.join(__dirname,'hmem-engine.mjs')}});
process.exit(result.status ?? 1);
