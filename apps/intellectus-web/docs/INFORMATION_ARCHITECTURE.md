# Guided diagnostic information architecture

Intellectus turns available public information into a focused,
consultant-reviewed starting point for the next client conversation.

## Route map

| Step | Route | Consultant task | Primary action |
| --- | --- | --- | --- |
| 1 | `/new-diagnostic` | Provide the organization, website, country, recent context period and conversation objective | Prepare diagnostic |
| 2 | `/overview` | Compare what the sample material suggests with what needs confirmation | Prepare client conversation |
| 3 | `/conversation` | Build a workshop agenda and add one consultant note | Save questions and continue |
| 4 | `/next-steps` | Review one action, two measures and a validation sequence | Add to conversation brief |
| 5 | `/brief` | Review the derived document | Mark ready for conversation |

`/` and unknown paths redirect to `/new-diagnostic`. Steps 2–5 redirect there
with a setup message when no result exists; Brief also requires a selected next
step. The application has no
sidebar, drawer, breadcrumbs or separate error page.

## Shared shell

The header contains the Intellectus brand, one Demo indicator and progress.
Desktop shows a compact horizontal sequence. Smaller screens show only the
current step number; Back and primary actions appear at the end of each page.
Future steps are disabled before a result exists. The Conversation brief
progress link appears after a next step has been added.

## Content model

The interface retains a validated diagnostic model behind plain-language
pages. The consultant's starting information, selected questions, chosen next
step and final review status remain in React memory for the current session.
No browser or remote persistence is used.
