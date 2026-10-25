// Local JSON-in/JSON-out bridge. Receives typed preferences, never service keys.
import fs from 'node:fs';
import path from 'node:path';
import { HMEM } from './hmem-engine.mjs';
const cataloguePath = new URL('./data/catalogue.json', import.meta.url);
const ALLOWED = new Set(fs.existsSync(cataloguePath)
  ? Object.keys(JSON.parse(fs.readFileSync(cataloguePath, 'utf8')).species)
  : ['Charizard', 'Venusaur', 'Blastoise']);
let lock, directory;
try {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (!/^[a-zA-Z0-9_-]{1,64}$/.test(input.profile || '')) throw new Error('Invalid profile.');
  if (typeof input.directory !== 'string') throw new Error('Missing memory directory.');
  directory = path.resolve(input.directory, input.profile);
  fs.mkdirSync(directory, {recursive: true});
  lock = fs.openSync(path.join(directory, 'bridge.lock'), 'wx');
  const chatId = 'doublescheck:' + input.profile;
  const memory = new HMEM({persistDir: directory, actor: 'doublescheck-user'});
  const active = key => memory.store.all().filter(r => r.chatId === chatId &&
    r.tags.includes('pref:' + key) && !r.supersededBy);
  // Validate the entire update and effective constraints under the profile lock,
  // before mutating either preference. Invalid requests cannot overwrite memory.
  const updates = input.updates || {};
  if (typeof updates !== 'object' || Array.isArray(updates)) throw new Error('Invalid updates.');
  for (const [key, value] of Object.entries(updates)) {
    if (!['favourite', 'avoided_partner'].includes(key)) throw new Error('Unknown preference.');
    if (!(value === null && key === 'avoided_partner') && !ALLOWED.has(value)) throw new Error('Unsupported demo species.');
  }
  const valueFor = key => Object.hasOwn(updates, key) ? updates[key] : active(key).at(-1)?.tags.find(t => t.startsWith('value:'))?.slice(6);
  const locked = input.locked_species || [];
  if (!Array.isArray(locked) || locked.length > 6 || locked.some(name => !ALLOWED.has(name))) throw new Error('Invalid locked species.');
  const effectiveAvoid = valueFor('avoided_partner');
  if (effectiveAvoid && (valueFor('favourite') === effectiveAvoid || locked.includes(effectiveAvoid))) throw new Error('Preference conflicts with avoidance.');
  for (const [key, value] of Object.entries(updates)) {
    if (!['favourite', 'avoided_partner'].includes(key)) throw new Error('Unknown preference.');
    const previous = active(key);
    if (value === null && key === 'avoided_partner') {
      for (const old of previous) memory.store.delete(old.id, 'User explicitly cleared partner avoidance');
      continue;
    }
    if (!ALLOWED.has(value)) throw new Error('Unsupported demo species.');
    if (previous.length === 1 && previous[0].tags.includes('value:' + value)) continue;
    const record = memory.add({
      content: key === 'favourite' ? `My favourite Pokemon is ${value}` : `Avoid partner ${value}`,
      type: 'preference', layer: 'working', confidence: 1,
      source: 'user_explicit', chatId,
      tags: ['project:doublescheck', 'pref:' + key, 'value:' + value],
      provenance: {origin: previous.length ? 'user_correction' : 'manual',
        learnedAt: Date.now(), label: 'Explicit DoublesCheck command-line preference'},
      ...(previous.length ? {supersedes: previous.at(-1).id} : {}),
    });
    for (const old of previous) memory.store.update(old.id, {supersededBy: record.id});
  }
  const queries = ['My favourite Pokemon', 'Avoid partner'];
  const recalls = queries.map(q => memory.query(q, {chatId}));
  const recalled = new Map();
  for (const result of recalls) for (const hit of result.memories) {
    if (hit.memory.chatId === chatId && !hit.memory.supersededBy) recalled.set(hit.memory.id, hit);
  }
  const resolved = {};
  for (const key of ['favourite', 'avoided_partner']) {
    const current = active(key);
    if (current.length > 1) throw new Error('Conflicting active preferences.');
    if (current.length && !recalled.has(current[0].id)) throw new Error('Stored preference below recall threshold; refusing to silently forget it.');
    if (current.length) resolved[key] = current[0].tags.find(t => t.startsWith('value:')).slice(6);
  }
  const memories = [...recalled.values()].map(hit => ({
    id: hit.memory.id, content: hit.memory.content, score: hit.relevance,
    source: hit.memory.source, provenance: hit.memory.provenance,
    layer: hit.memory.layer,
  }));
  console.log(JSON.stringify({engine: 'Meterless H-MEM reference + DoublesCheck facade',
    profile: input.profile, ...resolved, memories,
    context: memory.retrieval.formatReinjection([...recalled.values()]),
    retrieval_traces: recalls.map(r => r.trace)}));
} catch (error) {
  console.error(error?.code === 'EEXIST' ? 'Memory profile is busy; try again after the other run finishes.' : 'H-MEM operation failed: ' + error.message);
  process.exitCode = 1;
} finally {
  if (lock !== undefined) {
    fs.closeSync(lock);
    fs.unlinkSync(path.join(directory, 'bridge.lock'));
  }
}
