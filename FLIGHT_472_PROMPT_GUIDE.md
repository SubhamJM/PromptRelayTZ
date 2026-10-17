# Flight SW 472: Operational Crisis Prompt Engineering Guide (Tiers 1–5)

> Dedicated prompt engineering and tournament scoring guide for **Scenario 01: Airport Crisis (Flight SW 472 Emergency)**.
> Covers copy-paste prompt templates across all tournament score tiers (Tier 1 to Tier 5), itemized scoring breakdowns, and hard character/word limit compliance.

---

## 1. Quick Reference: Rules & Hard Length Constraints

### Hard Upper Limits per Turn
Each turn enforces hard limits at both frontend UI (real-time countdowns, input validation) and backend API (`HTTP 400 Bad Request`):

| Turn | Role | Max Words | Max Characters | Key Focus Directives |
| :--- | :--- | :---: | :---: | :--- |
| **Player 1** | Evidence Extractor | **80 words** | **600 chars** | CCTV & FIDS taxonomy, fact discrimination, noise filtering constraints |
| **Player 2** | Timeline Reconstructor | **80 words** | **600 chars** | Chronological sequencing, causal tracking, objective neutrality |
| **Player 3** | Logic Solver | **120 words** | **900 chars** | Airport Operational Rules (SEC-101, OPS-204), authorized dispatch action, strict JSON output |

### 100-Point Tournament Score Matrix
```
Total Score (100 pts) = Player 1 (20 pts) + Player 2 (20 pts) + Player 3 (20 pts) + Case Accuracy (40 pts)
```

| Grade Level | Score Range | Title | Expected Flight 472 Case Accuracy |
| :---: | :---: | :--- | :--- |
| **Tier 1** | **20 – 40 pts** | **Unsolved (F)** | Missing or undetermined action, no rules cited, missing bag clue |
| **Tier 2** | **40 – 60 pts** | **Apprentice Sleuth (C)** | Generic hold request, partial rules, circumstantial mention of bag |
| **Tier 3** | **60 – 80 pts** | **Investigator (B)** | Correct flight hold, citations of SEC-101/OPS-204, partial bag clue |
| **Tier 4** | **80 – 90 pts** | **Senior Sleuth (A)** | Complete operational hold directive, full rule citations, key bag details |
| **Tier 5** | **90 – 100 pts** | **Master Detective (S)** | Flawless 12/12 prompts across all turns + 40/40 perfect operational solution |

---

## 2. Scenario 01 Ground Truth Reference

To achieve full accuracy on the Flight 472 scenario, the final verdict must satisfy three core components:
1. **Authorized Operational Action (`culprit` / `action`)**: HOLD Flight SW 472 at Gate B07 immediately, suspend passenger boarding, cordon off the Gate B07 seating area, and dispatch the K9 explosive detection unit.
2. **Supporting Protocols (`method` / `rule_broken`)**: Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol).
3. **Decisive Evidence & Blocking Condition (`clue` / `evidence_keys`)**: Unattended blue hard-shell suitcase discovered at Gate B07 window seats reported at 08:49 awaiting K9 explosive clearance and passenger ownership verification (tag: Daniel Kim #SKW-78921-472).

---

## 3. Tier 1: Score 0 – 39 (Grade F • Unsolved)

### Scoring Profile
* **Player 1 Score**: **3 / 20 pts** *(Prompt: 1/12, Agent: 2/8)*
* **Player 2 Score**: **5 / 20 pts** *(Prompt: 3/12, Agent: 2/8)*
* **Player 3 Score**: **2 / 20 pts** *(Prompt: 1/12, Agent: 1/8)*
* **Case Accuracy**: **0 / 40 pts** *(Action: 0/15 missing, Method: 0/15 missing, Clue: 0/10 missing)*
* **Total Score**: **0 / 100 Points (Grade F • Unsolved)**
  *(Note: Non-rejected guesses lacking rules and evidence score between 15 – 30 pts)*

### Characteristics
* Short, generic prompts lacking role personas, entity taxonomies, negative constraints, and output format.
* Fails to guide Agent 1 to separate marathon news from CCTV logs, resulting in incomplete outputs and rejected verdicts.

### Prompts

#### Player 1 (Evidence Extractor)
```text
look at the airport evidence and tell me what happened with flight 472.
```
* **Stats**: 13 words, 71 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 0/3, Taxonomy: 1/3 (`flight`), Discrimination: 1/3 (`evidence`), Constraints: 0/3. Prompt Score = 1/12. Agent Execution = 2/8 (Incomplete).

#### Player 2 (Timeline Reconstructor)
```text
make a timeline of the airport events.
```
* **Stats**: 7 words, 38 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 0/3, Sequence: 2/3 (`timeline`), Connection: 1/3 (`events`), Neutrality: 0/3. Prompt Score = 3/12. Agent Execution = 2/8 (Incomplete).

#### Player 3 (Logic Solver)
```text
who is guilty at gate B07? tell me what to do.
```
* **Stats**: 11 words, 46 characters *(Limits: 120 words / 900 chars)*
* **Evaluator Breakdown**: Role: 0/3, Rules: 0/3, Action: 1/3, JSON Schema: 0/3. Prompt Score = 1/12. Agent Execution = 1/8.
* **Agent Output**: Returns conversational refusal or undetermined action placeholder (`"action": "Undetermined"`).

---

## 4. Tier 2: Score 40 – 59 (Grade C • Apprentice Sleuth)

### Scoring Profile
* **Player 1 Score**: **13 / 20 pts** *(Prompt: 5/12, Agent: 8/8)*
* **Player 2 Score**: **7 / 20 pts** *(Prompt: 5/12, Agent: 2/8)*
* **Player 3 Score**: **15 / 20 pts** *(Prompt: 7/12, Agent: 8/8)*
* **Case Accuracy**: **21 / 40 pts** *(Action: 8/15 partial, Method: 8/15 partial, Clue: 5/10 partial)*
* **Total Score**: **56 / 100 Points (Grade C • Apprentice Sleuth)**

### Characteristics
* Mentions basic actions and general gate location, but lacks explicit verification discrimination, noise filters, causal linkages, and multi-rule citations.
* Correctly halts Flight SW 472, but omits secondary containment/K9 deployments and cites only Rule SEC-101.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Examine the airport evidence. Extract the people, gates, and luggage from the CCTV files.
```
* **Stats**: 14 words, 87 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 1/3 (`examine`, `extract`), Taxonomy: 3/3 (`people`, `gate`, `luggage`, `cctv`), Discrimination: 1/3 (`evidence`), Constraints: 0/3. Prompt Score = 5/12. Agent Execution = 8/8.

#### Player 2 (Timeline Reconstructor)
```text
Organize the Gate B07 events in chronological sequence of what happened first and next.
```
* **Stats**: 14 words, 88 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 1/3 (`organize`), Sequence: 3/3 (`first`, `next`, `sequence`, `chronological`), Connection: 1/3 (`events`), Neutrality: 0/3. Prompt Score = 5/12. Agent Execution = 2/8.

#### Player 3 (Logic Solver)
```text
Analyze the situation at Gate B07 to determine the security action. Output in JSON format.
```
* **Stats**: 15 words, 90 characters *(Limits: 120 words / 900 chars)*
* **Evaluator Breakdown**: Role: 2/3 (`determine`), Rules: 1/3, Action: 2/3 (`security action`), JSON Schema: 2/3 (`json format`). Prompt Score = 7/12. Agent Execution = 8/8.
* **Agent Output**: Returns basic JSON schema (`{"action": "HOLD Flight SW 472 at Gate B07", "method": "Rule SEC-101", "clue": "Unattended blue bag"}`).

---

## 5. Tier 3: Score 60 – 74 (Grade B • Investigator)

### Scoring Profile
* **Player 1 Score**: **15 / 20 pts** *(Prompt: 7/12, Agent: 8/8)*
* **Player 2 Score**: **15 / 20 pts** *(Prompt: 7/12, Agent: 8/8)*
* **Player 3 Score**: **19 / 20 pts** *(Prompt: 11/12, Agent: 8/8)*
* **Case Accuracy**: **21 / 40 pts** *(Action: 8/15 partial, Method: 8/15 partial, Clue: 5/10 partial)*
* **Total Score**: **70 / 100 Points (Grade B • Investigator)**

### Characteristics
* Clear role personas, good taxonomies, sequencing words, and JSON format commands. Cites general airport operational protocols, but misses explicit citations of OPS-204 and the decisive baggage barcode tag.

### Prompts

#### Player 1 (Evidence Extractor)
```text
You are the evidence extractor. Extract the facts regarding Flight SW 472: identify people, locations, objects, and baggage. Record what occurred at Counter A04 and Gate B07.
```
* **Stats**: 27 words, 175 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`you are`, `evidence extractor`), Taxonomy: 3/3 (`people`, `locations`, `objects`, `baggage`), Discrimination: 1/3 (`facts`), Constraints: 0/3. Prompt Score = 7/12. Agent Execution = 8/8.

#### Player 2 (Timeline Reconstructor)
```text
You are the incident reconstructor. Organize all extracted airport events in chronological order: trace Daniel Kim and the blue bag from check-in to Gate B07.
```
* **Stats**: 25 words, 159 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`you are`, `incident reconstructor`), Sequence: 2/3 (`chronological`, `order`), Connection: 2/3 (`trace`, `from to`), Neutrality: 0/3. Prompt Score = 7/12. Agent Execution = 8/8.

#### Player 3 (Logic Solver)
```text
You are the decision agent. Analyze the Gate B07 timeline against airport operational protocols. Determine the security hold action for Flight SW 472. Output JSON format with keys: culprit, method, clue.
```
* **Stats**: 31 words, 203 characters *(Limits: 120 words / 900 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`you are`, `decision agent`), Rules: 3/3 (`operational protocols`), Action: 2/3 (`security hold action`), JSON Schema: 3/3 (`json format with keys: culprit, method, clue`). Prompt Score = 11/12. Agent Execution = 8/8.

---

## 6. Tier 4: Score 75 – 89 (Grade A • Senior Sleuth)

### Scoring Profile
* **Player 1 Score**: **17 / 20 pts** *(Prompt: 9/12, Agent: 8/8)*
* **Player 2 Score**: **16 / 20 pts** *(Prompt: 8/12, Agent: 8/8)*
* **Player 3 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Case Accuracy**: **35 / 40 pts** *(Action: 15/15 correct, Method: 15/15 correct, Clue: 5/10 partial)*
* **Total Score**: **88 / 100 Points (Grade A • Senior Sleuth)**

### Characteristics
* Highly disciplined prompts incorporating multi-source taxonomies, explicit verification discrimination, causal dependencies, and operational rule citations (SEC-101 and OPS-204).
* Decisive difference from Tier 5: Omits the baggage barcode tag (`#SKW-78921-472`) and passenger Daniel Kim cross-referencing in Player 3's output schema, capturing circumstantial evidence but not the decisive ownership link.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Role: Evidence Extractor. Extract verified facts from CCTV and incident logs: identify passengers, gate locations, and baggage. Distinguish confirmed facts from unverified passenger observations.
```
* **Stats**: 26 words, 196 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`Role: Evidence Extractor`), Taxonomy: 3/3 (`passengers`, `locations`, `baggage`), Discrimination: 3/3 (`distinguish confirmed facts from unverified`), Constraints: 0/3. Prompt Score = 9/12. Agent Execution = 8/8.

#### Player 2 (Timeline Reconstructor)
```text
Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 08:14 to 09:02. Connect causal links between the unattended bag and boarding status.
```
* **Stats**: 24 words, 168 characters *(Limits: 80 words / 600 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`Role: Incident Reconstructor`), Sequence: 2/3 (`chronological sequence`, `08:14 to 09:02`), Connection: 3/3 (`connect causal links`), Neutrality: 0/3. Prompt Score = 8/12. Agent Execution = 8/8.

#### Player 3 (Logic Solver)
```text
Role: Logic Decision Solver. Evaluate the timeline against Airport Operational Rules (SEC-101, OPS-204) to determine the operational dispatch action. Output strictly valid JSON format with keys: culprit, method, clue.
```
* **Stats**: 32 words, 224 characters *(Limits: 120 words / 900 chars)*
* **Evaluator Breakdown**: Role: 3/3 (`Role: Logic Decision Solver`), Rules: 3/3 (`Airport Operational Rules`, `SEC-101`, `OPS-204`), Action: 3/3 (`operational dispatch action`), JSON Schema: 3/3 (`strictly valid json format with keys`). Prompt Score = 12/12. Agent Execution = 8/8.
* **Agent Output**: Substantially deduces flight hold with boarding suspension and cites both rules SEC-101 and OPS-204 (Accuracy: 35/40 pts).

---

## 7. Tier 5: Score 90 – 100 (Grade S • Master Detective)

### Scoring Profile
* **Player 1 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 2 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 3 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Case Accuracy**: **40 / 40 pts** *(Culprit 15/15 + Method 15/15 + Decisive Clue 10/10)*
* **Expected Total Score**: **95 – 100 Points (Perfect Tournament Run)**

### Characteristics
* Masterclass prompt engineering hitting every single taxonomy, discrimination, causal, and constraint criterion while remaining comfortably beneath the hard length caps.
* Results in a complete extraction of the luggage tag barcode, an unbroken minute-by-minute timeline from 08:14 to 09:02, and an airtight multi-rule security verdict.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Role: Forensic Evidence Extractor.
Extract all factual evidence from CCTV, FIDS displays, baggage tags, and reports:
- Entities: passengers (Daniel Kim), officers, and gate personnel
- Times: exact camera and log timestamps
- Locations: Check-in Island A, Gate B07, Apron Bay
- Objects: blue hard-shell suitcase, baggage tag SKW-78921-472
Distinguish confirmed records from unverified chat observations. Filter out irrelevant marathon news. Do not decide dispatch actions.
```
* **Stats**: 66 words, 472 characters *(Hard Cap: 80 words / 600 chars)*
* **Evaluator Breakdown**:
  * Role & Persona: **3 / 3 pts** (`Role: Forensic Evidence Extractor`)
  * Taxonomy & Entities: **3 / 3 pts** (`passengers`, `times`, `locations`, `objects`, `tags`)
  * Fact Discrimination: **3 / 3 pts** (`Distinguish confirmed records from unverified chat observations`)
  * Noise Constraints: **3 / 3 pts** (`Filter out irrelevant marathon news`, `Do not decide dispatch actions`)
* **Total Player 1 Score**: Prompt 12/12 + Agent 8/8 = **20 / 20 pts**

#### Player 2 (Timeline Reconstructor)
```text
Role: Timeline & Incident Reconstructor.
Reconstruct the Gate B07 security incident into an exact chronological sequence:
- Sequence events by what occurred first, next, and last (08:14 check-in through 09:02 apron loading)
- Trace the unattended blue bag from check-in counter to Gate B07 window seating
- Connect causal links between unattended luggage and pre-departure boarding holds
Keep uncertain sightings separate. Maintain neutrality without issuing dispatch commands.
```
* **Stats**: 67 words, 477 characters *(Hard Cap: 80 words / 600 chars)*
* **Evaluator Breakdown**:
  * Role & Persona: **3 / 3 pts** (`Role: Timeline & Incident Reconstructor`)
  * Temporal Sequencing: **3 / 3 pts** (`first`, `next`, `last`, `chronological sequence`, `08:14 through 09:02`)
  * Movement & Causal Tracking: **3 / 3 pts** (`trace`, `connect causal links`, `unattended luggage`)
  * Neutrality & Uncertainty: **3 / 3 pts** (`keep uncertain sightings separate`, `maintain neutrality without issuing dispatch commands`)
* **Total Player 2 Score**: Prompt 12/12 + Agent 8/8 = **20 / 20 pts**

#### Player 3 (Logic Solver)
```text
Role: Logic Decision Solver.
Evaluate the reconstructed incident timeline against Airport Operational Rules (SEC-101, OPS-204, CLR-305) to determine the valid operational action:
- Specify the required operational dispatch action (HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9)
- Cite supporting rules (SEC-101, OPS-204)
- State the blocking condition (unattended blue suitcase awaiting K9 sweep)
Output strictly valid JSON with keys:
{
  "culprit": "<authorized action>",
  "method": "<supporting rules>",
  "motive": "<security hazard>",
  "rule_broken": "<rules violated>",
  "evidence_keys": ["<key clues>"]
}
```
* **Stats**: 83 words, 657 characters *(Hard Cap: 120 words / 900 chars)*
* **Evaluator Breakdown**:
  * Role & Persona: **3 / 3 pts** (`Role: Logic Decision Solver`)
  * Rules & Deductive Directives: **3 / 3 pts** (`Operational Rules`, `SEC-101`, `OPS-204`, `CLR-305`)
  * Operational Action Directives: **3 / 3 pts** (`authorized action`, `blocking condition`, `dispatch action`)
  * JSON Schema Mandate: **3 / 3 pts** (`strictly valid JSON with keys`, `{...}`)
* **Total Player 3 Score**: Prompt 12/12 + Agent 8/8 = **20 / 20 pts**

---

## 8. Expected Agent 3 Verdict JSON (Tier 5 Master Detective)

When Player 3 runs the Tier 5 prompt, Agent 3 produces the following structured JSON output:

```json
{
  "culprit": "HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9",
  "method": "Rule SEC-101 (Sterile Zone Unattended Baggage Protocol) and Rule OPS-204 (Pre-Departure Security Hold Protocol)",
  "motive": "Potential explosive hazard / sterile zone security breach from unverified unattended luggage",
  "rule_broken": "SEC-101, OPS-204",
  "evidence_keys": [
    "08:46 passenger report of unattended blue suitcase at Gate B07 window seats",
    "08:47:10 CCTV CAM 12 captures unidentified hooded individual fleeing Gate B07 corridor",
    "08:49:00 Security Incident Slip #SEC-0849 logged by Officer R. Nair",
    "Baggage Tag #SKW-78921-472 attached to bag belongs to passenger Daniel Kim (Flight SW 472)",
    "Awaiting K9 explosive sweep clearance before departure authorization under Rule CLR-305"
  ]
}
```

### Evaluator Synthesis Breakdown
* **Player 1 Score**: 20 / 20 pts
* **Player 2 Score**: 20 / 20 pts
* **Player 3 Score**: 20 / 20 pts
* **Culprit / Action ID**: **15 / 15 pts (CORRECT)** — Accurately deduced operational hold on Flight SW 472 with K9 deployment.
* **Method / Rules**: **15 / 15 pts (CORRECT)** — Cites Rule SEC-101 and Rule OPS-204.
* **Key Clue / Proof**: **10 / 10 pts (CORRECT)** — Cites unattended blue suitcase at Gate B07, tag SKW-78921-472, and K9 sweep blocking condition.
* **Format Compliance**: COMPLIANT (Structured JSON schema).
* **Final Match Total**: **100 / 100 Points (Grade S • Master Detective)**
