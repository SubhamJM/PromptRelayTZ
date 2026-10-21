# PromptRelay V2: Prompt Engineering Tiers & Score Guide

> Comprehensive tournament guide detailing verified prompt templates across all 5 score tiers (Tier 1 to Tier 5), itemized scoring breakdowns, exact grade brackets, and hard constraint compliance across all 4 operational and murder mystery scenarios.

---

## 1. Quick Reference: Scoring Architecture & Hard Limits

### Hard Upper Limits per Turn
Each turn enforces hard limits at both frontend UI (countdown counter, red border, disabled submit) and backend API (`HTTP 400 Bad Request`):

| Turn | Role | Max Words | Max Characters | Focus Directives |
| :--- | :--- | :---: | :---: | :--- |
| **Player 1** | Evidence Extractor | **80 words** | **600 chars** | Persona, entity categories, fact discrimination, noise filtering constraints |
| **Player 2** | Timeline Reconstructor | **80 words** | **600 chars** | Chronological sequencing, causal tracking, objective neutrality |
| **Player 3** | Logic Solver | **120 words** | **900 chars** | Rule analysis, operational action, strict JSON output schema |

### 100-Point Tournament Score Matrix
```
Total Score (100 pts) = Player 1 (20 pts) + Player 2 (20 pts) + Player 3 (20 pts) + Case Accuracy (40 pts)
```

| Grade Level | Score Range | Title | Expected Accuracy | Description |
| :---: | :---: | :--- | :--- | :--- |
| **Tier 1** | **0 – 39 pts** | **Unsolved (F)** | 0 / 40 pts | Failed deductions, missing schema, vague directives |
| **Tier 2** | **40 – 59 pts** | **Apprentice Sleuth (C)** | 21 / 40 pts | Basic prompts, partial entity tracking, circumstantial solve |
| **Tier 3** | **60 – 74 pts** | **Investigator (B)** | 21 / 40 pts | Strong taxonomy & chronology, protocol-based reasoning |
| **Tier 4** | **75 – 89 pts** | **Senior Sleuth (A)** | 35 / 40 pts | High prompt discipline, exact rule codes, near-complete solve |
| **Tier 5** | **90 – 100 pts** | **Master Detective (S)** | 40 / 40 pts | Full 12/12 prompts across all turns, flawless case deduction |

---

## 2. Tournament Test Verification Matrix

All 4 scenarios have been verified using automated regression test suites ([`tests/test_tools_and_distribution.py`](file:///home/ricing/Documents/code/Projects/PromptRelay_v2/tests/test_tools_and_distribution.py)), proving strict monotonic progression within each grade bracket:

| Scenario | Difficulty | Tier 1 (F: 0–39) | Tier 2 (C: 40–59) | Tier 3 (B: 60–74) | Tier 4 (A: 75–89) | Tier 5 (S: 90–100) | Progression |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **01: Airport Crisis (Flight SW 472)** | **Hard** *(Image+Text)* | 0 pts (F) | 56 pts (C) | 70 pts (B) | 88 pts (A) | 100 pts (S) | Strictly Increasing |
| **02: Blackwood Manor** | **Hard** *(Text)* | 0 pts (F) | 49 pts (C) | 70 pts (B) | 86 pts (A) | 99 pts (S) | Strictly Increasing |
| **03: Neon Nexus (SynthAI)** | **Hard** *(Text)* | 0 pts (F) | 48 pts (C) | 69 pts (B) | 84 pts (A) | 99 pts (S) | Strictly Increasing |
| **04: Velvet Vault (Vernissage)** | **Hard** *(Text)* | 0 pts (F) | 47 pts (C) | 69 pts (B) | 85 pts (A) | 99 pts (S) | Strictly Increasing |

> [!NOTE]
> **Equal Tournament Structural Parity**: All 3 text-based stories have been standardized to equal **Hard** difficulty, featuring identical structural complexity: exactly **4 suspects**, **3 evidence items**, **3 decoy items**, and **2 operational rules** per scenario for balanced, fair judging across competing teams.

---

## 3. Tier 1: Score 0 – 39 (Grade F • Unsolved)

### Scoring Profile
* **Player 1**: ~3 / 20 pts *(Prompt: 1/12, Agent: 2/8)*
* **Player 2**: ~5 / 20 pts *(Prompt: 2/12, Agent: 2/8)*
* **Player 3**: ~1 / 20 pts *(Prompt: 1/12, Agent: 0/8)*
* **Case Accuracy**: 0 / 40 pts *(No valid JSON, missing deductions)*
* **Total Score**: **0 Points (Unsolved • Grade F)**

### Characteristics
* One-line prompts lacking role directives, taxonomies, negative constraints, and output schema.
* Agent 3 fails to produce valid structured JSON (`was_clean_json = False`), triggering automatic rejection.

### Universal Tier 1 Prompts
```text
Player 1: get evidence from the file and tell me what happened.
Player 2: make a timeline of the events.
Player 3: who is guilty? give me the answer.
```

---

## 4. Tier 2: Score 40 – 59 (Grade C • Apprentice Sleuth)

### Scoring Profile
* **Player 1**: ~4 – 6 / 20 pts *(Prompt: 4–5/12, Agent: 2/8)*
* **Player 2**: ~7 / 20 pts *(Prompt: 5/12, Agent: 2/8)*
* **Player 3**: ~15 / 20 pts *(Prompt: 7/12, Agent: 8/8)*
* **Case Accuracy**: 21 / 40 pts *(Preliminary suspect 8/15, broad poison/override 8/15, circumstantial clue 5/10)*
* **Total Score**: **47 – 56 Points (Apprentice Sleuth • Grade C)**

### Characteristics
* Asks for basic entities and chronology, and requests JSON output with action verbs.
* Lacks specific operational rule codes, noise filtering, and alibi contradiction directives.

### Scenario-Specific Prompts

#### Scenario 01: Airport Crisis (Flight SW 472)
* **Player 1**: `Examine the airport evidence. Extract the people, gates, and luggage from the CCTV files.` *(14 words, 88 chars)*
* **Player 2**: `Organize the Gate B07 events in chronological sequence of what happened first and next.` *(14 words, 88 chars)*
* **Player 3**: `Analyze the situation at Gate B07 to determine the security action. Output in JSON format.` *(15 words, 90 chars)*
* **Score**: P1: 13, P2: 7, P3: 15, Case: 21 $\to$ **Total: 56 pts**

#### Scenario 02: Blackwood Manor
* **Player 1**: `Examine the evidence file. Extract the people, rooms, and tea items from the records.` *(14 words, 85 chars)*
* **Player 2**: `Organize the manor events in chronological sequence of what happened first and next.` *(13 words, 84 chars)*
* **Player 3**: `Analyze the situation at the manor to determine the culprit and action taken. Output in JSON format.` *(17 words, 100 chars)*
* **Score**: P1: 6, P2: 7, P3: 15, Case: 21 $\to$ **Total: 49 pts**

#### Scenario 03: Neon Nexus (SynthAI)
* **Player 1**: `Examine the cleanroom evidence. Extract the engineers, server rooms, and medical devices.` *(12 words, 89 chars)*
* **Player 2**: `Organize the cleanroom events in chronological sequence of what happened first and next.` *(13 words, 88 chars)*
* **Player 3**: `Analyze the situation in the cleanroom to determine the culprit and action taken. Output in JSON format.` *(17 words, 104 chars)*
* **Score**: P1: 5, P2: 7, P3: 15, Case: 21 $\to$ **Total: 48 pts**

#### Scenario 04: Velvet Vault (Vernissage Gallery)
* **Player 1**: `Examine the gallery evidence. Extract the guests, display vitrines, and art pieces.` *(12 words, 83 chars)*
* **Player 2**: `Organize the gallery events in chronological sequence of what happened first and next.` *(13 words, 86 chars)*
* **Player 3**: `Analyze the situation at the gallery to determine the culprit and action taken. Output in JSON format.` *(17 words, 102 chars)*
* **Score**: P1: 4, P2: 7, P3: 15, Case: 21 $\to$ **Total: 47 pts**

---

## 5. Tier 3: Score 60 – 74 (Grade B • Investigator)

### Scoring Profile
* **Player 1**: ~14 – 15 / 20 pts *(Prompt: 7/12, Agent: 8/8)*
* **Player 2**: ~15 / 20 pts *(Prompt: 7/12, Agent: 8/8)*
* **Player 3**: ~19 / 20 pts *(Prompt: 11/12, Agent: 8/8)*
* **Case Accuracy**: 21 / 40 pts *(Preliminary suspect 8/15, broad method 8/15, circumstantial clue 5/10)*
* **Total Score**: **69 – 70 Points (Investigator • Grade B)**

### Characteristics
* Professional personas, good taxonomies, chronological sequencing, and strict JSON schema commands.
* Cites general protocols/rules, but does NOT cite specific rule section codes or decisive forensic proof.

### Scenario-Specific Prompts

#### Scenario 01: Airport Crisis (Flight SW 472)
* **Player 1**: `You are the evidence extractor. Extract the facts regarding Flight SW 472: identify people, locations, objects, and baggage. Record what occurred at Counter A04 and Gate B07.` *(26 words, 177 chars)*
* **Player 2**: `You are the incident reconstructor. Organize all extracted airport events in chronological order: trace Daniel Kim and the blue bag from check-in to Gate B07.` *(24 words, 160 chars)*
* **Player 3**: `You are the decision agent. Analyze the Gate B07 timeline against airport operational protocols. Determine the security hold action for Flight SW 472. Output JSON format with keys: culprit, method, clue.` *(31 words, 206 chars)*
* **Score**: P1: 15, P2: 15, P3: 19, Case: 21 $\to$ **Total: 70 pts**

#### Scenario 02: Blackwood Manor
* **Player 1**: `You are the evidence extractor. Extract the facts regarding Blackwood Manor: identify people, times, locations, and tea items. Record what occurred in the drawing room and study.` *(26 words, 178 chars)*
* **Player 2**: `You are the incident reconstructor. Organize all extracted manor events in chronological order: trace Dr. Bell and the tea tray from the drawing room to the study.` *(27 words, 163 chars)*
* **Player 3**: `You are the decision agent. Analyze the manor timeline against forensic protocols. Determine the culprit and method for Lord Reginald's death. Output JSON format with keys: culprit, method, clue.` *(29 words, 196 chars)*
* **Score**: P1: 15, P2: 15, P3: 19, Case: 21 $\to$ **Total: 70 pts**

#### Scenario 03: Neon Nexus (SynthAI)
* **Player 1**: `You are the evidence extractor. Extract the facts regarding SynthAI cleanroom: identify people, times, locations, and medical devices. Record what occurred in Cleanroom 03 and server pods.` *(26 words, 186 chars)*
* **Player 2**: `You are the incident reconstructor. Organize all extracted cleanroom events in chronological order: trace Marcus Vance and the insulin pump from the cleanroom to the lounge.` *(25 words, 172 chars)*
* **Player 3**: `You are the decision agent. Analyze the cleanroom timeline against cyber-physical protocols. Determine the culprit and method for Dr. Rostova's death. Output JSON format with keys: culprit, method, clue.` *(28 words, 203 chars)*
* **Score**: P1: 14, P2: 15, P3: 19, Case: 21 $\to$ **Total: 69 pts**

#### Scenario 04: Velvet Vault (Vernissage Gallery)
* **Player 1**: `You are the evidence extractor. Extract the facts regarding Vernissage Gallery: identify people, times, locations, and vitrines. Record what occurred in the private vault and Grand Rotunda.` *(26 words, 187 chars)*
* **Player 2**: `You are the incident reconstructor. Organize all extracted gallery events in chronological order: trace Julian Thorne and the display vitrine from the rotunda to the vault.` *(25 words, 169 chars)*
* **Player 3**: `You are the decision agent. Analyze the gallery timeline against forensic art crime protocols. Determine the culprit and method for Delacroix's death. Output JSON format with keys: culprit, method, clue.` *(28 words, 201 chars)*
* **Score**: P1: 14, P2: 15, P3: 19, Case: 21 $\to$ **Total: 69 pts**

---

## 6. Tier 4: Score 75 – 89 (Grade A • Senior Sleuth)

### Scoring Profile
* **Player 1**: ~14 – 17 / 20 pts *(Prompt: 9/12, Agent: 8/8)*
* **Player 2**: ~16 / 20 pts *(Prompt: 8/12, Agent: 8/8)*
* **Player 3**: ~19 – 20 / 20 pts *(Prompt: 11–12/12, Agent: 8/8)*
* **Case Accuracy**: 35 / 40 pts *(Confirmed culprit 15/15, full method/rules 15/15, physical clue without decisive link 5/10)*
* **Total Score**: **84 – 88 Points (Senior Sleuth • Grade A)**

### Characteristics
* Highly disciplined prompts incorporating multi-source taxonomies, fact discrimination (`confirmed` vs `unverified`), and causal tracking.
* Cites the exact scenario-specific rule codes (`SEC-101/OPS-204`, `Standard §102`, `Standard §404`, `Standard §201`), advancing the case deduction to full culprit and method, but omitting decisive evidence_keys.

### Scenario-Specific Prompts

#### Scenario 01: Airport Crisis (Flight SW 472)
* **Player 1**: `Role: Evidence Extractor. Extract verified facts from CCTV and incident logs: identify passengers, gate locations, and baggage. Distinguish confirmed facts from unverified passenger observations.` *(23 words, 194 chars)*
* **Player 2**: `Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 08:14 to 09:02. Connect causal links between the unattended bag and boarding status.` *(22 words, 169 chars)*
* **Player 3**: `Role: Logic Decision Solver. Evaluate the timeline against Airport Operational Rules (SEC-101, OPS-204) to determine the operational dispatch action. Output strictly valid JSON format with keys: culprit, method, clue.` *(30 words, 221 chars)*
* **Score**: P1: 17, P2: 16, P3: 20, Case: 35 $\to$ **Total: 88 pts**

#### Scenario 02: Blackwood Manor
* **Player 1**: `Role: Evidence Extractor. Extract verified facts from the manor dossier: identify people, room locations, and tea items. Distinguish confirmed facts from unverified staff rumors.` *(23 words, 180 chars)*
* **Player 2**: `Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 8:00 to 9:15 PM. Connect causal links between the unattended tea tray and poisoning.` *(24 words, 171 chars)*
* **Player 3**: `Role: Logic Decision Solver. Evaluate the timeline against Forensic Trace Standard §102 and Timeline Discrepancy Principle to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue.` *(31 words, 233 chars)*
* **Score**: P1: 16, P2: 16, P3: 19, Case: 35 $\to$ **Total: 86 pts**

#### Scenario 03: Neon Nexus (SynthAI)
* **Player 1**: `Role: Evidence Extractor. Extract verified facts from cleanroom logs and device telemetry: identify engineers, server rooms, and medical devices. Distinguish confirmed facts from unverified statements.` *(24 words, 198 chars)*
* **Player 2**: `Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 22:00 to 23:45. Connect causal links between the wireless transmission and pump bolus.` *(23 words, 172 chars)*
* **Player 3**: `Role: Logic Decision Solver. Evaluate the timeline against Cyber-Physical Forensics Standard §404 and Alibi Integrity Rule to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue.` *(30 words, 230 chars)*
* **Score**: P1: 14, P2: 16, P3: 19, Case: 35 $\to$ **Total: 84 pts**

#### Scenario 04: Velvet Vault (Vernissage Gallery)
* **Player 1**: `Role: Evidence Extractor. Extract verified facts from gallery dossiers and toxicology reports: identify guests, vault locations, and vitrines. Distinguish confirmed facts from unverified observations.` *(23 words, 199 chars)*
* **Player 2**: `Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 20:30 to 22:45. Connect causal links between the coated vitrine latch and Delacroix poisoning.` *(23 words, 178 chars)*
* **Player 3**: `Role: Logic Decision Solver. Evaluate the timeline against Biological Trace Principle §201 and Property Recovery Presumption to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue.` *(30 words, 235 chars)*
* **Score**: P1: 15, P2: 16, P3: 19, Case: 35 $\to$ **Total: 85 pts**

---

## 7. Tier 5: Score 90 – 100 (Grade S • Master Detective)

### Scoring Profile
* **Player 1**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 2**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 3**: **19 – 20 / 20 pts** *(Prompt: 11–12/12, Agent: 8/8)*
* **Case Accuracy**: **40 / 40 pts** *(Confirmed culprit 15/15 + precise mechanism 15/15 + decisive alibi contradiction & proof 10/10)*
* **Total Score**: **99 – 100 Points (Master Detective • Grade S)**

### Characteristics
* Masterclass prompt engineering fulfilling all 4 rubric criteria on every turn (Role, Taxonomy, Discrimination, Noise Constraints, Sequencing, Causal Tracking, Neutrality, Schema).
* Incorporates specific `evidence_keys` directives, compelling the solver to extract decisive physical proofs and unmask alibi contradictions.

### Scenario-Specific Master Detective Prompts

#### Scenario 01: Airport Crisis (Flight SW 472)
* **Player 1**:
  ```text
  Role: Forensic Evidence Extractor. Extract all factual evidence from CCTV, FIDS displays, baggage tags, and reports: - Entities: passengers (Daniel Kim), officers, and gate personnel - Times: exact camera and log timestamps - Locations: Check-in Island A, Gate B07, Apron Bay - Objects: blue hard-shell suitcase, baggage tag SKW-78921-472. Distinguish confirmed records from unverified chat observations. Filter out irrelevant marathon news. Do not decide dispatch actions.
  ```
  *(66 words, 495 chars)*
* **Player 2**:
  ```text
  Role: Timeline & Incident Reconstructor. Reconstruct the Gate B07 security incident into an exact chronological sequence: - Sequence events by what occurred first, next, and last (08:14 check-in through 09:02 apron loading) - Trace the unattended blue bag from check-in counter to Gate B07 window seating - Connect causal links between unattended luggage and pre-departure boarding holds. Keep uncertain sightings separate. Maintain neutrality without issuing dispatch commands.
  ```
  *(64 words, 487 chars)*
* **Player 3**:
  ```text
  Role: Logic Decision Solver. Evaluate the reconstructed incident timeline against Airport Operational Rules (SEC-101, OPS-204, CLR-305) to determine the valid operational action: - Specify the required operational dispatch action (HOLD Flight SW 472 at Gate B07 immediately, suspend boarding, cordon seating, dispatch K9) - Cite supporting rules (SEC-101, OPS-204) - State the blocking condition (unattended blue suitcase awaiting K9 sweep) Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys
  ```
  *(74 words, 559 chars)*
* **Score**: P1: 20, P2: 20, P3: 20, Case: 40 $\to$ **Total: 100 pts (Grade S)**

#### Scenario 02: Blackwood Manor
* **Player 1**:
  ```text
  Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: identify people (Dr. Bell, Higgins, Charles, Beatrice), timestamps (8:00 to 9:15 PM), locations (study, cellar, drawing room, greenhouse), and objects (Earl Grey tea, Demerara sugar, silver sugar tongs, muddy boots). Distinguish confirmed facts from uncertain observations. Ignore kitchen fire chatter. Do not accuse anyone.
  ```
  *(58 words, 436 chars)*
* **Player 2**:
  ```text
  Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: order events by what happened first, next, and last with exact timestamps from 8:00 PM tea preparation to 9:15 PM discovery. Trace suspect movements and connect causal dependencies showing how the unattended tea tray allowed poison delivery. Keep uncertain sightings separate. Maintain neutrality without naming a culprit.
  ```
  *(62 words, 469 chars)*
* **Player 3**:
  ```text
  Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Forensic Trace Standard §102, Timeline Discrepancy Principle) to determine the final resolution: deduce the true culprit, explain the potassium cyanide sugar tongs method, and identify decisive physical evidence_keys (red peat mud boots greenhouse alibi contradiction and sugar tongs residue). Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys
  ```
  *(66 words, 506 chars)*
* **Score**: P1: 20, P2: 20, P3: 19, Case: 40 $\to$ **Total: 99 pts (Grade S)**

#### Scenario 03: Neon Nexus (SynthAI)
* **Player 1**:
  ```text
  Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: identify people (Marcus Vance, Dr. Elena Rostova, Chloe Lin), timestamps (22:00 to 23:45), locations (Class-10 cleanroom, cubicles, lounge), and objects (Omnipod insulin pump, BLE sniffer, Pi Zero dongle, USB power bank). Distinguish confirmed logs from unverified statements. Ignore cooling manifold noise. Do not accuse anyone.
  ```
  *(58 words, 442 chars)*
* **Player 2**:
  ```text
  Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: order events by what happened first, next, and last with exact timestamps from 22:15 entry to 23:45 discovery. Trace suspect movements and connect causal dependencies linking the 22:42:14 BLE transmission to the fatal insulin bolus. Keep unverified alibis separate. Maintain neutrality without naming a culprit.
  ```
  *(61 words, 461 chars)*
* **Player 3**:
  ```text
  Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Cyber-Physical Forensics Standard §404, Alibi Integrity Rule) to determine the final resolution: deduce the true culprit, explain the remote BLE insulin override method, and identify decisive evidence_keys (concealed Pi Zero MAC D4:8A:3F:11:C9:82 in drawer and automated cron commit alibi contradiction). Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys
  ```
  *(66 words, 513 chars)*
* **Score**: P1: 20, P2: 20, P3: 19, Case: 40 $\to$ **Total: 99 pts (Grade S)**

#### Scenario 04: Velvet Vault (Vernissage Gallery)
* **Player 1**:
  ```text
  Role: Forensic Evidence Extractor. Extract all verified facts from the dossier and evidence feeds: identify people (Julian Thorne, Henri Delacroix, Cecile Moreau, Monique De Valois), timestamps (20:30 to 22:45), locations (Grand Rotunda, private vault, restroom, terrace), and objects (vitrine latch, nitrile gloves, Caesarean Emerald, lavender talc). Distinguish confirmed facts from uncertain rumors. Ignore broken champagne glass noise. Do not accuse anyone.
  ```
  *(60 words, 470 chars)*
* **Player 2**:
  ```text
  Role: Timeline & Incident Reconstructor. Using the extracted facts, reconstruct the incident into a strict chronological sequence: order events by what happened first, next, and last with exact timestamps from 20:30 preview to 21:40 collapse. Trace suspect movements and connect causal dependencies showing how the coated vitrine latch caused Delacroix transdermal poisoning. Keep unverified sightings separate. Maintain neutrality without naming a culprit.
  ```
  *(60 words, 458 chars)*
* **Player 3**:
  ```text
  Role: Logic Decision Solver. Analyze the reconstructed timeline alongside operational rules (Biological Trace Principle §201, Property Recovery Presumption) to determine the final resolution: deduce the true culprit, explain the tetrodotoxin coated vitrine latch method, and identify decisive evidence_keys (discarded nitrile gloves with Julian Thorne DNA and stolen Caesarean Emerald in briefcase). Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys
  ```
  *(66 words, 524 chars)*
* **Score**: P1: 20, P2: 20, P3: 19, Case: 40 $\to$ **Total: 99 pts (Grade S)**

---

## 8. Evaluator Rubric Keyword Reference

When composing tournament prompts, ensure you hit the critical tokens evaluated by [`backend/app/graph/evaluator.py`](file:///home/ricing/Documents/code/Projects/PromptRelay_v2/backend/app/graph/evaluator.py):

### Player 1 (Evidence Extractor)
* **Role (3 pts)**: `role`, `you are`, `expert`, `specialist`, `agent`, `engine`, `extractor`, `analyst`
* **Taxonomy (3 pts)**: Needs 4+ of: `people`, `who`, `time`, `location`, `place`, `object`, `item`, `movement`
* **Discrimination (3 pts)**: `confirmed`, `uncertain`, `unverified`, `alleged`, `verified`, `distinguish`, `separate`
* **Noise Constraints (3 pts)**: Must include **both** a filter (`noise`, `irrelevant`, `ignore`, `filter`, `chatter`) **and** a negative constraint (`do not`, `never`, `refrain`, `without`, `no infer`)

### Player 2 (Timeline Reconstructor)
* **Role (3 pts)**: `role`, `you are`, `reconstructor`, `investigator`, `specialist`, `agent`
* **Sequencing (3 pts)**: Needs `first` OR `next` OR `sequence` + (`chronological`, `timeline`, `order`, `minute`, `timestamp`)
* **Causal Tracking (3 pts)**: Needs `connect` OR `depend` + (`movement`, `lead`, `caused`, `relationship`)
* **Neutrality (3 pts)**: Needs **both** an uncertainty marker (`uncertain`, `separate`, `unverified`) **and** a neutrality constraint (`do not`, `neutral`, `without naming`, `no verdict`)

### Player 3 (Logic Solver)
* **Role (3 pts)**: `role`, `you are`, `solver`, `detective`, `magistrate`, `decision`, `determine`, `solve`
* **Rules & Deduction (3 pts)**: Needs `rule` OR `deduc` + (`regulat`, `support`, `eliminat`, `policy`, `condition`)
* **Operational Action (3 pts)**: Needs `action` OR `blocking` OR `resume` + (`culprit`, `method`, `clue`, `decision`)
* **JSON Schema (3 pts)**: Must include `json` **and** schema keywords (`key`, `schema`, `format`, `strict`, `{`)
