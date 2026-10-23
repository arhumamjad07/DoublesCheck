// Application facade over the unmodified, pinned Apache-2.0 H-MEM reference.
import { HMEM as ReferenceHMEM } from './vendor/hmem/compiled/reference/src/index.mjs';
export class HMEM extends ReferenceHMEM {
  query(text, options) {
    const result = super.query(text, options);
    // The reference touches access counters on reads; persist those across CLI runs.
    this.store.persist();
    return result;
  }
}
