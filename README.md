# Evidence Contradiction Registry

A bounded GenLayer intelligent-contract primitive for preserving **conflicting documentation evidence** without letting repeated supporting excerpts outvote one contradiction. This is a text-relation ledger, not a truth oracle or automated adjudicator.

## Verified hosted simulator run (2026-11-16)

- Contract: `0x653142ECa3c69ebAb4D48d6A72029B7884755753`
- [Studio](https://studio.genlayer.com/?import-contract=0x653142ECa3c69ebAb4D48d6A72029B7884755753) · [Explorer](https://explorer-studio.genlayer.com/address/0x653142ECa3c69ebAb4D48d6A72029B7884755753)
- Source SHA-256: `8a50e698d3f3972a832fea020be6cf39bbefd471677e3b28a2ac2381366fa6bc`
- Eight successful FINALIZED transactions: deployment, three additions, three semantic reviews and a final snapshot.
- Stored relations: release → SUPPORTS; known-issues → CONTRADICTS; unrelated theme → INSUFFICIENT.
- Final immutable snapshot `complete` → CONFLICT, revision 3, every registered excerpt reviewed.
- The supporting review records 3 agree, 1 disagree and 1 idle; this is majority consensus, not unanimity. The other receipts preserve their actual vote counts.
- Source hash, transaction identities and final stored state are checked by `npm run verify`. Public receipt projections and state are in `evidence/`.

## What is new

Unlike proposal deduplication or delivery review, this contract separates immutable claims, curated source excerpts, independent semantic assessments and immutable revision-bound snapshots. It detects contradictions in submitted text and makes the conflict persistent rather than generating one persuasive summary.

A software release editor can use it to compare release notes, a known-issues note and a feature announcement about the same scoped claim. The demonstration uses invented Cedar release notes only, with no real product, payments, legal or medical decisions.

## State machine

1. Deployment fixes one claim, context and curator.
2. `add_evidence(id, source_id, excerpt, citation)` appends an immutable excerpt. At most eight excerpts, one per curator-supplied source ID. Whitespace/case-normalized exact duplicates are rejected across sources. Citation is a provenance label, **not fetched or verified**.
3. `review(id, expected_revision)` runs semantic inference through GenLayer. The leader produces SUPPORTS, CONTRADICTS or INSUFFICIENT plus exact quote anchors. Every validator independently repeats the semantic task, then agrees only on the same relation. Shape/quote checks alone are not consensus.
4. `snapshot(id, expected_revision)` requires every currently registered excerpt to be reviewed, aggregates deterministically, and freezes an immutable revision-specific snapshot. Appending new evidence does not rewrite old snapshots; the new revision cannot be snapshotted until reviewed.

| Relations present | Snapshot status |
|---|---|
| supporting and contradicting | CONFLICT |
| contradicting only (possibly insufficient) | CONTRADICTED |
| supporting only (possibly insufficient) | SUPPORTED_BY_SUBMITTED_TEXT |
| only insufficient | INSUFFICIENT |

One contradiction beats any number of supporting sources for the purpose of detecting a conflict. No source-majority weighting, acceptance threshold, payment or binding action exists. `SUPPORTED_BY_SUBMITTED_TEXT` is deliberately **not TRUE**: it may coexist with insufficient excerpts and does not assert completeness of external evidence.

Read methods: `get_state`, `get_evidence`, `get_decision`, `get_snapshot`. Missing records return `{}`.

## Local verification

37 direct-SDK tests pass using `genlayer-test==0.29.2`, Python 3.12 and GenVM SDK `v0.3.0-rc7`. LLM outputs are mocked in these tests; they establish state-machine and validator behavior, not model accuracy. Tests cover stale revisions, incomplete snapshots, new evidence after completed review, immutable snapshots and decisions, bounds, capacity, source and content duplicate rejection, conflicting evidence, malformed output, forged quotes, independent validator disagreement and differing valid anchors.

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-test.txt
pytest -q
```

The runner loader currently asks for an older release-asset name. The official `genvm-runners-all.tar.xz` from https://github.com/genlayerlabs/genvm/releases/tag/v0.3.0-rc7 must be saved as `~/.cache/gltest-direct/genvm-universal-v0.3.0-rc7.tar.xz`. A workspace-local HOME can be used where the default cache is read-only.

## Live simulator reproduction

```
npm install
npm run demo
npm run demo -- --authorized-studionet-only
npm run verify
npm run test:receipts
```

The demo refuses any chain other than hosted Studionet 61999 with zero gas price. It creates an isolated disposable signer in ignored `.local/`, never loads the user's wallet, sends no value and uses five configured simulator validators in NORMAL mode. Do not fund this signer. Checkpoint files prevent blind retries after uncertain submissions. The public verifier uses no signer or write method.

Live deployment status and receipt availability are recorded in `evidence/`; a submitted hash is not proof of completion. All live claims must be supported by verified FINALIZED receipts and matching deployed source.

## Limitations and threat model

- The curator can omit evidence, choose biased context, censor contributions, mislabel citations or invent source IDs. Source IDs do **not** establish source independence or identity. Duplicate detection prevents only normalized exact replay, not paraphrases or collusion.
- Excerpts and claims are untrusted data. Prompt isolation, quote checks and independent consensus mitigate but do not eliminate prompt injection or semantic errors.
- The contract assesses textual relations only. It does not fetch URLs, verify document authorship, detect later document edits or establish real-world truth.
- A snapshot is complete only relative to its registered, bounded evidence set at its revision. Consumers must inspect its revision against current state; older snapshots remain readable and may be obsolete.
- Incorrect immutable records cannot be edited. Start a new claim instance with corrected input and retain the prior audit trail.
- Hosted Studionet is a simulator using model-backed validator roles, not a decentralized production validator network. Majority agreement is not unanimity or proof of accuracy.
- No financial, healthcare, legal, employment or eligibility outcomes are implemented.

## Attribution

New evidence-registry contract, state machine and tests. GenLayer supplies SDK and test runner. The network safety/journaling and receipt-validation scaffolding are adapted from this user's earlier Semantic Proposal Registry; that reuse is explicit. The claim/evidence contract and synthetic scenarios are separate, not a renamed submission.
