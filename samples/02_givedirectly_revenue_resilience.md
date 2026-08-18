# GiveDirectly

## Revenue Resilience — Public-Search P0 Report

> **Scope:** Retained Project 3 P0 run based on public search metadata.
> It surfaces evidence for consultant review; it is not a complete
> financial assessment or client diagnosis.

- **Run ID:** `RUN-PAOLA-P0-001`
- **Controlled state:** `ok`
- **Organization:** GiveDirectly
- **Website:** https://www.givedirectly.org
- **Research provider:** `duckduckgo_html`
- **Execution path:** 21_WEB_SEARCH -> 30_EVIDENCE_PIPELINE -> 40_RAG_RETRIEVAL_PIPELINE -> 51_REVENUE_RESILIENCE_AGENT

## Finding

Public search results surfaced revenue-resilience signals that should be reviewed before drawing conclusions about funding mix or concentration.

- **Finding type:** observed
- **Confidence:** 58%
- **Requires validation:** Yes
- **Validation question:** Which revenue sources are material, recurring, or concentrated in the current financial year?

## Public sources surfaced

- `SRC-001` — [All Financials by Year - GiveDirectly](https://www.givedirectly.org/financials-by-year) (official; authority: official)
- `SRC-002` — [Financials | GiveDirectly](https://www.givedirectly.org/financials) (official; authority: official)
- `SRC-003` — [Givedirectly Inc - Nonprofit Explorer - ProPublica](https://projects.propublica.org/nonprofits/organizations/271661997) (third-party; authority: unknown)
- `SRC-004` — [Givedirectly — Financials & Trends (990)](https://www.roundpaper.com/nonprofits/org/givedirectly-inc-271661997) (third-party; authority: unknown)
- `SRC-005` — [Givedirectly Inc - Audit for period ending Dec 2024 - Nonprofit ...](https://projects.propublica.org/nonprofits/display_audit/2024-12-GSAFAC-0000381190) (third-party; authority: unknown)

## Evidence ledger

- **EV-001:** Public source "All Financials by Year - GiveDirectly" contains revenue-resilience search signals: 990, financial.
  - Sources: `SRC-001`
  - Confidence: 68%
  - Status: supported
- **EV-002:** Public source "Financials | GiveDirectly" contains revenue-resilience search signals: 990, finance, financial.
  - Sources: `SRC-002`
  - Confidence: 68%
  - Status: supported
- **EV-003:** Public source "Givedirectly Inc - Nonprofit Explorer - ProPublica" contains revenue-resilience search signals: revenue.
  - Sources: `SRC-003`
  - Confidence: 52%
  - Status: supported
- **EV-004:** Public source "Givedirectly — Financials & Trends (990)" contains revenue-resilience search signals: 990, financial, grant, grants, report.
  - Sources: `SRC-004`
  - Confidence: 52%
  - Status: supported
- **EV-005:** Public source "Givedirectly Inc - Audit for period ending Dec 2024 - Nonprofit ..." contains revenue-resilience search signals: revenue.
  - Sources: `SRC-005`
  - Confidence: 52%
  - Status: supported

## Unknowns

- **UNK-001:** Revenue concentration and recurrence cannot be determined from the P0 public search slice alone.

## Retrieved framework context

### Funding Concentration

Revenue resilience assessment should check whether an organization depends heavily on one grant, donor, contract, or funder. Public evidence may reveal named funding sources, but concentration percentages are often unknown without internal financial data.

**Evaluation use:** Use this when evidence mentions grants, funders, annual reports, or revenue sources. Do not infer concentration unless amounts or proportions are available.

### Financial Resilience Limitations

Public-data-first diagnostics must separate facts from hypotheses. Missing financial evidence should remain unknown. Do not invent revenue numbers, donor concentration, cash runway, operating reserves, or growth rates.

**Evaluation use:** Use this as a guardrail for all revenue resilience findings.

### Revenue Diversification

Diversification considers whether public signals show multiple revenue types such as individual donations, grants, corporate partnerships, government contracts, memberships, or earned income. Public signals can support an observed finding that multiple revenue channels are described, but cannot prove resilience by themselves.

**Evaluation use:** Use this when evidence mentions donations, grants, partnerships, fundraising, revenue, or financial reports.

## Consultant review decision

Do not infer revenue concentration, reserves, runway, or resilience
from these search results. Review the underlying financial statements
and ask which sources are material, recurring, or concentrated in the
current financial year.

## Limitations

- No revenue numbers are inferred from search metadata.
- Missing financial evidence remains unknown rather than negative.
- Search metadata can identify relevant sources but does not replace
  source-document review.
- The retained run does not establish financial health or client outcomes.

## Artifact provenance

Generated deterministically from:

- `runs/paola_p0_givedirectly.json`
- `scripts/generate_sample_reports.py`
