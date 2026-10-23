// Generated from pinned Meterless H-MEM source; see UPSTREAM.json.
import fs from "node:fs";
import path from "node:path";
export class TrustLedgerService {
    clock;
    entries = [];
    file;
    constructor(clock, persistDir){
        this.clock = clock;
        if (persistDir) {
            this.file = path.join(persistDir, "ledger.jsonl");
            if (fs.existsSync(this.file)) {
                this.entries = fs.readFileSync(this.file, "utf-8").split("\n").filter(Boolean).map((l)=>JSON.parse(l));
            }
        }
    }
    log(memoryId, action, actor, extra) {
        const entry = {
            memoryId,
            action,
            actor,
            timestamp: this.clock(),
            ...extra
        };
        this.entries.push(entry);
        if (this.file) fs.appendFileSync(this.file, JSON.stringify(entry) + "\n", "utf-8");
        return entry;
    }
    history(memoryId) {
        return this.entries.filter((e)=>e.memoryId === memoryId);
    }
    all() {
        return this.entries;
    }
    stats() {
        const out = {};
        for (const e of this.entries)out[e.action] = (out[e.action] ?? 0) + 1;
        return out;
    }
}
