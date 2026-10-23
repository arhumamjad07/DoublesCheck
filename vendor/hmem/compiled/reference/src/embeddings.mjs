// Generated from pinned Meterless H-MEM source; see UPSTREAM.json.
const DIM = 64;
export function tokenize(text) {
    return text.toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter((t)=>t.length > 1);
}
function fnv1a(str) {
    let h = 0x811c9dc5;
    for(let i = 0; i < str.length; i++){
        h ^= str.charCodeAt(i);
        h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
}
export function embed(text) {
    const vec = new Array(DIM).fill(0);
    for (const token of tokenize(text)){
        const h = fnv1a(token);
        const idx = h % DIM;
        const sign = (h >>> 8) % 2 === 0 ? 1 : -1;
        const mag = 1 + (h >>> 16) % 8 / 8;
        vec[idx] += sign * mag;
    }
    const norm = Math.sqrt(vec.reduce((s, v)=>s + v * v, 0));
    return norm === 0 ? vec : vec.map((v)=>v / norm);
}
export function cosine(a, b) {
    let dot = 0;
    for(let i = 0; i < a.length; i++)dot += a[i] * b[i];
    return dot;
}
export function jaccard(a, b) {
    const sa = new Set(a);
    const sb = new Set(b);
    if (sa.size === 0 || sb.size === 0) return 0;
    let inter = 0;
    for (const x of sa)if (sb.has(x)) inter++;
    return inter / (sa.size + sb.size - inter);
}
