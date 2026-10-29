import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { fitIsolationForest, isolationTrace, lofScores, rankOf, recallAtBudget } from "./engine.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
function spearman(a, b) {
  const ra = rankOf(a), rb = rankOf(b), n = a.length;
  const ma = (n + 1) / 2; let sab = 0, sa = 0, sb = 0;
  for (let i = 0; i < n; i++) { const x = ra[i] - ma, y = rb[i] - ma; sab += x * y; sa += x * x; sb += y * y; }
  return sab / Math.sqrt(sa * sb);
}
for (const img of ["img1", "img2", "img3"]) {
  const D = JSON.parse(readFileSync(path.join(root, "web/src/data/lab", `${img}.json`)));
  const py = JSON.parse(readFileSync(path.join(root, ".cache", `lab_validate_${img}.json`)));
  const X = D.rows.map((r) => Float32Array.from(r.x));
  const isT = D.rows.map((r) => !!r.t);
  let t0 = performance.now();
  const f = fitIsolationForest(X, { seed: 42 });
  const tFit = performance.now() - t0;
  const sIF = X.map((x) => f.score(x));
  t0 = performance.now();
  const sLOF = lofScores(X, 20);
  const tLof = performance.now() - t0;
  const rec = (s) => recallAtBudget(rankOf(s), isT, 0.05).toFixed(3);
  // trace sanity
  let pt = 0, nt = 0, cT = 0, cN = 0, bad = 0;
  X.forEach((x, i) => {
    const tr = isolationTrace(f, x, 0);
    for (let q = 0; q < 5; q++) { const L = isolationTrace(f, x, q).length; if (isT[i]) { pt += L; cT++; } else { nt += L; cN++; } }
    if (tr.length && !(tr[0].lo.length === x.length)) bad++;
  });
  console.log(`${img}: IF spearman=${spearman(sIF, py.if).toFixed(3)} recall@5% js=${rec(sIF)} sk=${rec(py.if)} | LOF spearman=${spearman(sLOF, py.lof).toFixed(3)} recall@5% js=${rec(sLOF)} sk=${rec(py.lof)}`);
  console.log(`   fit ${tFit.toFixed(0)}ms, lof ${tLof.toFixed(0)}ms, mean trace depth target=${(pt / cT).toFixed(2)} nontarget=${(nt / cN).toFixed(2)} ${pt / cT < nt / cN ? "OK" : "FAIL"}`);
}
