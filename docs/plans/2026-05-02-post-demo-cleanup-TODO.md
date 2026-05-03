# Post-Demo-Recording Cleanup — TODO

**Created:** 2026-05-02
**Owner:** Umesh
**Trigger:** Run after the KGC 2026 demo recording is captured.

The demo-v3 edits are deliberately left **uncommitted in the working tree** so the recording session has the latest scripted content + assets without a fresh checkout. Once the recording is done, work this list top-to-bottom.

---

## Current state of working tree (do not commit until after recording)

- [ ] `R` `docs/demo-v3/narration.md` → `archive/docs/demo/narration-v3.md` (rename, staged; `archive/` is gitignored, so this removes the file from tracked tree)
- [ ] `R` `docs/demo-v3/run-demo.sh` → `archive/docs/demo/run-demo-v3.sh` (rename, staged; same effect as above)
- [ ] `M` `docs/demo-v3/demo-script.md` (frontmatter v3.2.0→v3.2.2, S8 added, Block 1 reframed with analyst-inside-a-question + wrong-tool-for-enterprise-graph contrast, Block 3 schema beat trimmed to pay for it, Polycapture replaces QuickTime in production checklist, PNG title-card reference added)
- [ ] `??` `docs/demo-v3/epistract.png` (1536×1024 schematic, untracked — needs `git add`)

## Decisions still needed

### B. Local-disk cache cleanup (no git effect)

- [ ] `epistract-output/` (2.5M) — **delete locally?** Regenerable from a corpus. Cheap to keep.
- [ ] `.DS_Store` recursive — delete (16K). Safe.
- [ ] `.pytest_cache/`, `.ruff_cache/`, `scripts/.pytest_cache/` — delete (~450K). Regenerable.
- Keep: `.kreuzberg/` (slow to rebuild), `.claude/` (session state), `.planning/` (GSD), `.venv/` (slow), `archive/`, `docs/blog/`, `docs/epistract.mp4`.

### C. Tracked-but-orphaned candidates (touches git)

- [ ] `docs/screenshots/epistract-architecture.png` — only referenced from `docs/blog/...` (gitignored) → orphan in public tree. **Remove from tracked tree, or keep as a generic asset?**
- [ ] `docs/diagrams/v2/{architecture,data-flow,two-layer-kg}.html` — `v2`-era HTML diagrams; active versions are sibling `.svg` files. **Move to `archive/docs/diagrams-v2/`, or keep?**

### D. Scope

- [ ] **Docs-only commit, or sweep `paper/`, `tests/`, `core/`, `examples/`, `commands/` for stale content too?** Code dirs need careful per-file inspection.

## Execution sequence (after decisions are made)

1. Apply B decisions (local rm only, no git impact).
2. Apply C decisions (`git rm` or `git mv` to `archive/`).
3. Stage demo-v3 changes:
   ```bash
   git add docs/demo-v3/epistract.png docs/demo-v3/demo-script.md
   # the two renames are already staged
   ```
4. Commit:
   ```bash
   git commit -m "docs(demo-v3): tighten 5-min KGC cut, add schematic, archive 12-min variant"
   ```
5. (If C/D removals happened) optionally a second commit:
   ```bash
   git commit -m "docs: archive stale v2-era diagrams + orphaned assets"
   ```
6. Push: `git push origin main`.
7. Verify no open PRs remain: `gh pr list --state open` (was none at 2026-05-02 09:xx).

## Notes

- Open PRs at TODO creation: **none** (`gh pr list --state open` was empty).
- The demo-script `Prior 12-min cut` line points to `archive/docs/demo/narration-v3.md` + `run-demo-v3.sh` — those paths exist locally but are gitignored. After commit + push, the link is technically dead from a fresh clone's perspective. Decide whether to re-tag the line as "available locally only" or drop it.
- The PNG schematic subtitle reads `v3.2.0` — kept as-is per Umesh's call; architecture is unchanged across v3.2.x patches.
