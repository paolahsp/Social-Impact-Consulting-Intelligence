# Paola 22 Website Extraction

Scope:

`22_WEBSITE_EXTRACTION` plus `DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST`

Architecture v1 remains frozen. This implementation does not configure Firecrawl, add credentials, create new production workflows, draw consulting conclusions, or begin workflow 23.

## Provider

- Development provider: Jina Reader
- Endpoint pattern: `https://r.jina.ai/http://{host}{path}`
- Credentials: none
- Production candidate: Firecrawl (not configured in this task)

## Input Contract

Required organization fields:

- `organization_name`
- `website` or `official_url`
- `country`

The same values may be supplied inside `run_context.organization`.

## Output Contract

- `controlled_state`: `success`, `no_relevant_content`, or `request_failure`
- `sources`: official website records following `source.schema.json`
- `website_context`: public page signals only
- `errors`: explicit page-level failures

Website context contains:

- `mission_signals`
- `program_signals`
- `impact_signals`
- `fundraising_signals`
- `stakeholder_entry_points`
- `report_links`

## Evidence Boundary

The workflow preserves `FACT ≠ INFERENCE ≠ HYPOTHESIS ≠ UNKNOWN`. It records public page content and source metadata. Missing pages or missing content remain unknown and never become claims about organizational efficiency, performance, or consulting need.

## Repository Test

The repository contains a deterministic validator and a network harness mirroring the eight Jina Reader page candidates used by n8n.

Status: implementation reconstructed and verified on 10 August 2026 after the earlier local changes were found not to have reached the remote feature branch. Structural and fixture validation are recorded through the repository validation commands below.

## Live n8n Test

Status: **LIVE n8n VERIFIED** on 10 August 2026.

The DEV workflow contains two branches:

1. GiveDirectly (`https://www.givedirectly.org`) happy path.
2. Reserved `.invalid` domain controlled-failure path.

Stored workflow IDs:

- `22_WEBSITE_EXTRACTION`: `azDD2e5wihHdfZYr`
- `DEV_PAOLA_22_WEBSITE_EXTRACTION_TEST`: `RIdoB60VUKg7H5de`

Final executions:

- DEV two-branch execution: `1277` — succeeded in 5.618 seconds.
- GiveDirectly child execution: `1278` — succeeded in 3.943 seconds.
- Invalid-domain child execution: `1279` — succeeded in 364 milliseconds.

Observed GiveDirectly output:

- `controlled_state`: `success`
- `pages_attempted`: `8`
- `sources`: `6`, all on the official `givedirectly.org` domain with unique IDs and URLs
- useful page types: `home`, `about`, `careers`, `financials`, `fundraising`, `contact`
- `website_context`: non-empty mission, program, impact, and fundraising signals; fundraising/contact stakeholder entry points; financials report link
- page-level errors: `2` (`/our-work` and `/annual-reports` returned no usable Jina Reader content)

Observed invalid-domain output:

- `controlled_state`: `request_failure`
- `pages_attempted`: `8`
- `sources`: `0`
- `errors`: `8` explicit DNS-resolution failures
- all website-context arrays remained empty; no content or conclusions were fabricated

Runtime corrections made during the live test:

1. Replaced unavailable `URL` constructor usage in the n8n Code node with deterministic string/regex URL normalization.
2. Correlated Jina responses with candidates by array index instead of `$itemIndex`, preventing duplicate `SRC-WEB-001` IDs and root URLs.
3. Treated provider-rendered “Page not found” content as a request failure.
4. Reclassified the `/impact` redirect titled “GiveDirectly jobs | GiveDirectly openings” as `careers` and excluded it from `report_links`.
5. Expanded mission-signal matching to cover explicit language about helping people living in poverty.

Known limitations:

- Candidate paths are generic and do not perform site-specific link discovery.
- Jina Reader is the credential-free development provider; Firecrawl remains unconfigured.
- `runs/paola_22_*.json` are compact evidence snapshots of the observed final output. n8n retains the full extracted page text.

## Commands

```powershell
python scripts\generate_n8n_skeletons.py
python scripts\validate_n8n_skeletons.py
python scripts\validate_fixtures.py
python scripts\validate_paola_22_output.py runs\paola_22_givedirectly.json
python scripts\validate_paola_22_output.py runs\paola_22_invalid_website.json
```

Local network harness:

```powershell
python scripts\paola_22_website_extraction_test.py --org-name "GiveDirectly" --website "https://www.givedirectly.org" --country "United States" --output runs\paola_22_givedirectly.json
python scripts\paola_22_website_extraction_test.py --org-name "Invalid Website Test" --website "https://this-domain-must-not-exist.invalid" --country "Test" --simulate-failure --output runs\paola_22_invalid_website.json
```
