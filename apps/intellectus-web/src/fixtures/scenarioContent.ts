export type DiagnosticScenario = 'funding' | 'impact' | 'operations' | 'neutral'

interface LensContent {
  title: string
  suggests: string
  confirm: string
  detail: string
}

export interface ScenarioContent {
  summary: string[]
  findings: string[]
  missing: string[]
  hypotheses: string[]
  questions: Array<{ key: string; text: string; reason: string }>
  recommendation: { key: string; title: string; description: string; rationale: string }
  kpis: Array<{ key: string; title: string; baseline: string }>
  roadmap: Array<{ title: string; period: string; objective: string; activities: string[] }>
}

const lenses: Record<DiagnosticScenario, LensContent> = {
  funding: {
    title: 'Funding resilience',
    suggests: 'Public material may describe funding sources, commitments and reported financial context.',
    confirm: 'The dependable funding mix, planning assumptions and current constraints still need confirmation.',
    detail: 'Compare public statements with the funding assumptions used for current decisions.',
  },
  impact: {
    title: 'Impact and evidence',
    suggests: 'Public material may describe intended outcomes, reported results and evaluation activity.',
    confirm: 'The evidence used for current decisions, learning and accountability still needs confirmation.',
    detail: 'Clarify which measures leaders use, how they interpret them and where evidence remains incomplete.',
  },
  operations: {
    title: 'Operations and stakeholder experience',
    suggests: 'Public material may describe services and stakeholder support without showing the full internal journey.',
    confirm: 'Ownership, handoffs and the path from a reported issue to resolution still need confirmation.',
    detail: 'Use one recent issue to understand responsibilities, information needs and stakeholder updates.',
  },
  neutral: {
    title: 'Conversation focus',
    suggests: 'The stated challenge provides an initial direction for the conversation.',
    confirm: 'The precise decision, scope and useful outcome still need to be agreed with the client.',
    detail: 'Begin by agreeing what decision the conversation should support and what is currently uncertain.',
  },
}

const sharedLenses: LensContent[] = [lenses.funding, lenses.impact, lenses.operations]

export function orderedLenses(scenario: DiagnosticScenario) {
  if (scenario === 'neutral') return sharedLenses
  return [lenses[scenario], ...sharedLenses.filter((lens) => lens !== lenses[scenario])]
}

const baseline = 'Baseline not established'

export const scenarioContent: Record<DiagnosticScenario, ScenarioContent> = {
  funding: {
    summary: [
      'The diagnostic is focused on funding resilience and the assumptions behind current planning.',
      'Available public material may provide context, but the current funding mix and constraints require client confirmation.',
      'The workshop should clarify exposure, decision points and the first baseline to establish.',
    ],
    findings: [
      'Available public material may describe reported income sources and funding commitments.',
      'It does not establish which income is dependable for current planning.',
    ],
    missing: ['Which funding sources are dependable, restricted or exposed to near-term change?', 'Which planning decisions are most sensitive to funding uncertainty?', 'How are funding risks reviewed and acted on?'],
    hypotheses: ['Income concentration may affect planning flexibility.', 'Restrictions attached to funding may shape delivery choices.', 'The timing of funding decisions may influence operational commitments.'],
    questions: [
      { key: 'question-1', text: 'Which funding sources are most dependable for current planning?', reason: 'This separates recurring support from income that may be less predictable.' },
      { key: 'question-2', text: 'Where is funding concentration creating the most concern?', reason: 'This helps identify exposure without assuming that concentration is already a problem.' },
      { key: 'question-3', text: 'Which funds have restrictions that shape delivery decisions?', reason: 'This clarifies how available income can actually be used.' },
      { key: 'question-4', text: 'What decisions would change if expected income arrived later or not at all?', reason: 'This reveals the assumptions that matter most to continuity.' },
      { key: 'question-5', text: 'Which measures do you use to review funding resilience?', reason: 'This establishes how the client currently recognizes and monitors risk.' },
    ],
    recommendation: { key: 'next-step', title: 'Map the funding assumptions behind one priority plan', description: 'List the expected sources, restrictions, timing and decisions that depend on them before discussing responses.', rationale: 'This creates a bounded view of exposure and shows which assumptions need evidence or client confirmation.' },
    kpis: [{ key: 'coverage', title: 'Committed funding coverage', baseline }, { key: 'concentration', title: 'Funding concentration ratio', baseline }],
    roadmap: [
      { title: 'Validate', period: 'Days 0–30', objective: 'Confirm the funding assumptions and decisions that matter most.', activities: ['Map one priority plan', 'Confirm sources and restrictions', 'Define both baselines'] },
      { title: 'Design', period: 'Days 31–60', objective: 'Develop a bounded response to the confirmed exposure.', activities: ['Compare practical options', 'Choose one response to test', 'Agree review criteria'] },
      { title: 'Pilot', period: 'Days 61–90', objective: 'Test the agreed response and review what changes.', activities: ['Run the agreed test', 'Observe the measures', 'Decide whether to adapt or stop'] },
    ],
  },
  impact: {
    summary: [
      'The diagnostic is focused on how impact information supports current decisions and learning.',
      'Available public material may describe outcomes, but the evidence used internally requires client confirmation.',
      'The workshop should connect one priority decision to the measures and learning it needs.',
    ],
    findings: ['Available public material may describe intended outcomes and reported results.', 'It does not establish how current evidence influences a specific management decision.'],
    missing: ['Which decisions should the available impact information support?', 'Where are outcome definitions or measures still unclear?', 'How is learning reviewed and translated into action?'],
    hypotheses: ['Measures may not answer the decisions that matter most.', 'Evidence may be reviewed differently across teams.', 'Learning cycles may affect how quickly practice can adapt.'],
    questions: [
      { key: 'question-1', text: 'Which decision most needs stronger impact information?', reason: 'This grounds the discussion in a practical use for evidence.' },
      { key: 'question-2', text: 'Which outcomes matter most for that decision?', reason: 'This helps distinguish essential outcomes from broader reporting.' },
      { key: 'question-3', text: 'What evidence do you currently trust, and why?', reason: 'This clarifies confidence and the standards already in use.' },
      { key: 'question-4', text: 'Where are important results still difficult to interpret?', reason: 'This identifies uncertainty without treating missing evidence as failure.' },
      { key: 'question-5', text: 'How does learning lead to a change in practice?', reason: 'This connects measurement to the way decisions are made.' },
    ],
    recommendation: { key: 'next-step', title: 'Map the evidence needed for one priority decision', description: 'Define the decision, relevant outcomes, available measures, confidence limits and the next learning question.', rationale: 'This keeps measurement focused on a real decision and reveals where evidence is useful or incomplete.' },
    kpis: [{ key: 'coverage', title: 'Priority outcome evidence coverage', baseline }, { key: 'learning', title: 'Decision learning cycle time', baseline }],
    roadmap: [
      { title: 'Validate', period: 'Days 0–30', objective: 'Confirm one priority decision and the evidence it needs.', activities: ['Define the decision', 'Review available measures', 'Record confidence limits'] },
      { title: 'Design', period: 'Days 31–60', objective: 'Shape a proportionate learning approach.', activities: ['Compare evidence options', 'Choose one learning test', 'Agree review criteria'] },
      { title: 'Pilot', period: 'Days 61–90', objective: 'Test the learning approach on a limited scale.', activities: ['Run the agreed test', 'Review what it reveals', 'Decide whether to adapt or stop'] },
    ],
  },
  operations: {
    summary: [
      'The diagnostic is focused on the journey from a reported stakeholder issue to resolution.',
      'Available public material may describe services, but ownership and handoffs require client confirmation.',
      'The workshop should map one real journey and agree how progress could be measured.',
    ],
    findings: ['Available public material may describe services and stakeholder support.', 'It does not establish the complete internal issue-resolution journey.'],
    missing: ['Who owns an issue from report to resolution?', 'Where do handoffs happen between teams or roles?', 'How is the stakeholder kept informed?'],
    hypotheses: ['Ownership may change across issue types.', 'Handoffs may affect elapsed resolution time.', 'Available information may influence first-contact resolution.'],
    questions: [
      { key: 'question-1', text: 'When a stakeholder reports an issue, what happens next?', reason: 'This opens with a real journey rather than an assumed process.' },
      { key: 'question-2', text: 'Who is responsible at each stage?', reason: 'This clarifies who makes decisions and who stays involved.' },
      { key: 'question-3', text: 'Where does ownership change?', reason: 'This identifies handoffs where context or responsibility may change.' },
      { key: 'question-4', text: 'How is the stakeholder kept informed?', reason: 'This keeps stakeholder experience visible during the discussion.' },
      { key: 'question-5', text: 'Which measures show that an issue has been resolved well?', reason: 'This helps define success before setting a target.' },
    ],
    recommendation: { key: 'next-step', title: 'Map one recent stakeholder issue from report to resolution', description: 'Document each stage, owner, handoff, required information and stakeholder update before discussing solutions.', rationale: 'This creates a shared view of the current journey and shows where evidence or ownership is still missing.' },
    kpis: [{ key: 'cycle-time', title: 'Issue-resolution cycle time', baseline }, { key: 'first-owner-rate', title: 'First-owner resolution rate', baseline }],
    roadmap: [
      { title: 'Validate', period: 'Days 0–30', objective: 'Build a shared view of the current journey before deciding what should change.', activities: ['Map one recent issue', 'Confirm owners and handoffs', 'Define both baselines'] },
      { title: 'Design', period: 'Days 31–60', objective: 'Shape a bounded improvement from what the client confirms.', activities: ['Compare practical options', 'Choose a small test', 'Agree review criteria'] },
      { title: 'Pilot', period: 'Days 61–90', objective: 'Test an approved change on a limited scale.', activities: ['Run the agreed test', 'Observe the measures', 'Decide whether to adapt or stop'] },
    ],
  },
  neutral: {
    summary: [
      'The diagnostic begins with the challenge described in the setup.',
      'The local demo does not establish which diagnostic lens should lead without further client context.',
      'The workshop should clarify the decision, scope and most useful next question.',
    ],
    findings: ['The stated challenge provides a starting point, but the local demo contains no reviewed organization-specific findings.'],
    missing: ['What decision should this diagnostic help the client make?', 'Which part of the challenge is most urgent or consequential?', 'What information would make the first conversation useful?'],
    hypotheses: ['The initial challenge may contain more than one decision.', 'Different stakeholders may define the priority differently.', 'The most useful evidence may depend on the decision that is clarified first.'],
    questions: [
      { key: 'question-1', text: 'What decision should this conversation help you make?', reason: 'This establishes the practical purpose before exploring explanations.' },
      { key: 'question-2', text: 'Which part of the challenge matters most right now?', reason: 'This helps set a manageable scope.' },
      { key: 'question-3', text: 'Who experiences the challenge most directly?', reason: 'This identifies the perspectives needed in the conversation.' },
      { key: 'question-4', text: 'What have you already tried or learned?', reason: 'This avoids repeating work and surfaces useful context.' },
      { key: 'question-5', text: 'What would a useful next step make clearer?', reason: 'This defines a proportionate outcome for the workshop.' },
    ],
    recommendation: { key: 'next-step', title: 'Define one decision and the information it needs', description: 'Agree the decision, scope, people involved and the most important unanswered question before discussing solutions.', rationale: 'This prevents a broad challenge from being treated as a confirmed diagnosis.' },
    kpis: [{ key: 'decision', title: 'Decision scope agreed', baseline }, { key: 'questions', title: 'Priority information gaps resolved', baseline }],
    roadmap: [
      { title: 'Validate', period: 'Days 0–30', objective: 'Clarify the decision, scope and information needs.', activities: ['Agree the priority decision', 'Identify key perspectives', 'Record open questions'] },
      { title: 'Design', period: 'Days 31–60', objective: 'Shape a bounded response to what is confirmed.', activities: ['Compare practical options', 'Choose one small test', 'Agree review criteria'] },
      { title: 'Pilot', period: 'Days 61–90', objective: 'Test the agreed response without assuming wider change.', activities: ['Run the agreed test', 'Review what it reveals', 'Decide whether to adapt or stop'] },
    ],
  },
}
