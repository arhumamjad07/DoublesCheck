// Generated from pinned Meterless H-MEM source; see UPSTREAM.json.
import { MemoryStoreService } from "./memoryStore.mjs";
import { TrustLedgerService } from "./trustLedger.mjs";
import { MemoryMiningService } from "./memoryMining.mjs";
import { MemoryRetrievalService } from "./memoryRetrieval.mjs";
import { ConflictDetectionService } from "./conflictDetection.mjs";
import { SleepCycleService } from "./sleepCycle.mjs";
import { DreamingService } from "./dreaming.mjs";
export * from "./types.mjs";
export { MemoryStoreService } from "./memoryStore.mjs";
export { TrustLedgerService } from "./trustLedger.mjs";
export { MemoryMiningService, parseStrictJsonArray } from "./memoryMining.mjs";
export { MemoryRetrievalService } from "./memoryRetrieval.mjs";
export { ConflictDetectionService } from "./conflictDetection.mjs";
export { SleepCycleService } from "./sleepCycle.mjs";
export { DreamingService } from "./dreaming.mjs";
export { embed, cosine, tokenize, jaccard } from "./embeddings.mjs";
export class HMEM {
    ledger;
    store;
    mining;
    retrieval;
    conflicts;
    sleep;
    dreaming;
    clock;
    constructor(opts = {}){
        this.clock = opts.clock ?? Date.now;
        const actor = opts.actor ?? "system";
        this.ledger = new TrustLedgerService(this.clock, opts.persistDir);
        this.store = new MemoryStoreService(this.clock, this.ledger, actor, opts.persistDir);
        this.mining = new MemoryMiningService(this.store, this.clock, opts.minerFn);
        this.retrieval = new MemoryRetrievalService(this.store, this.ledger, this.clock, actor);
        this.conflicts = new ConflictDetectionService(this.store, this.ledger, this.clock, actor);
        this.sleep = new SleepCycleService(this.store, this.ledger, this.clock, actor);
        this.dreaming = new DreamingService(this.store, this.ledger, this.clock, actor);
    }
    add(input) {
        return this.store.add(input);
    }
    mine(event, text, opts) {
        return this.mining.mineInteraction(event, text, opts);
    }
    query(query, opts) {
        return this.retrieval.query(query, opts);
    }
    feedback(memoryId, kind) {
        this.retrieval.feedback(memoryId, kind);
    }
}
