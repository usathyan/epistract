---
phase: 12
slug: domain-list-and-delete-commands
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-07
---

# Phase 12 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| CLI argv → manage_domains.py | `sys.argv[2]` (domain name) is untrusted; path traversal possible if used directly in path construction | Domain name string (untrusted) |
| manage_domains.py → filesystem | `shutil.rmtree` and `shutil.move` are irreversible; name must be validated before calling | Domain directory path (sensitive) |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-12-02 | Tampering | `cmd_archive` / `cmd_remove`: domain name arg in path construction | mitigate | `_validate_active_name()` enumerates `DOMAINS_DIR.iterdir()` into a set first; name must appear in set before any path is constructed — rejects traversal strings like `../secrets` | closed |
| T-12-03 | Tampering | `cmd_archive`: collision could silently overwrite existing archived domain | mitigate | `(ARCHIVED_DIR / name).exists()` checked before `shutil.move`; returns error JSON with explicit message if collision detected | closed |
| T-12-04 | Tampering | `cmd_remove`: bare directories without `domain.yaml` could be accidentally deleted | mitigate | Both active and archived removal paths verify `(path / "domain.yaml").exists()` before calling `shutil.rmtree` | closed |

*Status: open · closed*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-07 | 3 | 3 | 0 | gsd-secure-phase (orchestrator verify) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-07
