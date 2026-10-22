# Riverton Museum Heist: The Celestial Madonna Prompt Engineering Guide (Tiers 1–5)

> Dedicated prompt engineering and tournament scoring guide for **Scenario 05: The Riverton Museum Heist (The Celestial Madonna)**.
> Covers copy-paste prompt templates across all tournament score tiers (Tier 1 to Tier 5), itemized scoring breakdowns, hard character/word limit compliance, and full evidence linkages.

---

## 1. Quick Reference: Rules & Hard Length Constraints

### Hard Upper Limits per Turn
Each turn enforces hard limits at both frontend UI (real-time countdowns, input validation) and backend API (`HTTP 400 Bad Request`):

| Turn | Role | Max Words | Max Characters | Key Focus Directives |
| :--- | :--- | :---: | :---: | :--- |
| **Player 1** | Evidence Extractor | **80 words** | **600 chars** | CCTV, SCADA telemetry, spectrometry, evidence locker items, fact discrimination, noise filtering constraints |
| **Player 2** | Timeline Reconstructor | **80 words** | **600 chars** | Chronological sequencing, causal tracking between blackout and transit, objective neutrality |
| **Player 3** | Logic Solver | **120 words** | **900 chars** | Museum Art Crime Rules (SEC-401, ART-302, CLR-505), culprit identification, strict JSON output schema |

### 100-Point Tournament Score Matrix
```
Total Score (100 pts) = Player 1 (20 pts) + Player 2 (20 pts) + Player 3 (20 pts) + Case Accuracy (40 pts)
```

| Grade Level | Score Range | Title | Expected Museum Heist Case Accuracy |
| :---: | :---: | :--- | :--- |
| **Tier 1** | **0 – 39 pts** | **Unsolved (F)** | Missing or undetermined action, no rules cited, missing clue |
| **Tier 2** | **40 – 59 pts** | **Apprentice Sleuth (C)** | Unconfirmed suspect, partial method, circumstantial locker mention (21/40 pts) |
| **Tier 3** | **60 – 74 pts** | **Investigator (B)** | Correct suspect, general protocol reasoning, circumstantial clue (21/40 pts) |
| **Tier 4** | **75 – 89 pts** | **Senior Sleuth (A)** | Confirmed culprits, exact rule codes (SEC-401, ART-302), physical memo clue (35/40 pts) |
| **Tier 5** | **90 – 100 pts** | **Master Detective (S)** | Flawless 12/12 prompts across all turns + 40/40 perfect case deduction & alibi disproof |

---

## 2. Scenario 05 Ground Truth Reference

To achieve full accuracy on the Riverton Museum Heist scenario, the final verdict must satisfy three core components:
1. **Primary Conspirators (`culprit`)**: Dr. Julian Vance (Head of Art Conservation) as the inside mastermind and Chief Marcus Thorne as the security accomplice.
2. **Breach Method & Rules (`method` / `rule_broken`)**: Breaker B-04 intentional blackout exploiting 90-second auxiliary power failover to swap original canvas with synthetic acrylic forgery and drop tube at Locker 14 under Rule SEC-401 and Rule ART-302.
3. **Decisive Evidence & Alibi Contradiction (`clue` / `evidence_keys`)**: Conservation staff access card #408 (CONSV-408) and Private Vault cloakroom token C-408 recovered from Locker 14, matching Dr. Julian Vance (Badge CONSV-04 / Conservation), Thorne's sub-station sabotage alibi contradiction, and modern acrylic forgery RM-1887-04.

---

## 3. Tier 1: Score 0 – 39 (Grade F • Unsolved)

### Scoring Profile
* **Player 1 Score**: ~3 / 20 pts *(Prompt: 1/12, Agent: 2/8)*
* **Player 2 Score**: ~5 / 20 pts *(Prompt: 3/12, Agent: 2/8)*
* **Player 3 Score**: ~2 / 20 pts *(Prompt: 1/12, Agent: 1/8)*
* **Case Accuracy**: 0 / 40 pts *(No valid JSON or undetermined placeholder)*
* **Total Score**: **0 / 100 Points (Grade F • Unsolved)**

### Characteristics
* Generic one-line prompts lacking role personas, entity taxonomies, negative constraints, and output format.
* Fails to guide Agent 1 to separate catering noise from SCADA and CCTV logs.

### Prompts

#### Player 1 (Evidence Extractor)
```text
look at the museum evidence and tell me what happened to the painting.
```
* **Stats**: 13 words, 70 characters *(Limits: 80 words / 600 chars)*

#### Player 2 (Timeline Reconstructor)
```text
make a timeline of the museum events.
```
* **Stats**: 7 words, 37 characters *(Limits: 80 words / 600 chars)*

#### Player 3 (Logic Solver)
```text
who stole the painting? tell me what to do.
```
* **Stats**: 9 words, 43 characters *(Limits: 120 words / 900 chars)*

---

## 4. Tier 2: Score 40 – 59 (Grade C • Apprentice Sleuth)

### Scoring Profile
* **Player 1 Score**: ~13 / 20 pts *(Prompt: 5/12, Agent: 8/8)*
* **Player 2 Score**: ~7 / 20 pts *(Prompt: 5/12, Agent: 2/8)*
* **Player 3 Score**: ~16 / 20 pts *(Prompt: 8/12, Agent: 8/8)*
* **Case Accuracy**: 21 / 40 pts *(Culprit: 8/15 partial, Method: 8/15 partial, Clue: 5/10 partial)*
* **Total Score**: **57 / 100 Points (Grade C • Apprentice Sleuth)**

### Characteristics
* Requests basic entities and chronological sequencing, and prompts for JSON output.
* Lacks specific operational rule codes, noise filtering, and alibi contradiction directives.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Examine the museum evidence. Extract the people, galleries, and art items from the CCTV files.
```
* **Stats**: 15 words, 94 characters *(Limits: 80 words / 600 chars)*

#### Player 2 (Timeline Reconstructor)
```text
Organize the Gallery 4 events in chronological sequence of what happened first and next.
```
* **Stats**: 14 words, 88 characters *(Limits: 80 words / 600 chars)*

#### Player 3 (Logic Solver)
```text
Analyze the situation in Gallery 4 to determine the culprit and action taken. Output in JSON format.
```
* **Stats**: 17 words, 100 characters *(Limits: 120 words / 900 chars)*

---

## 5. Tier 3: Score 60 – 74 (Grade B • Investigator)

### Scoring Profile
* **Player 1 Score**: ~15 / 20 pts *(Prompt: 7/12, Agent: 8/8)*
* **Player 2 Score**: ~15 / 20 pts *(Prompt: 7/12, Agent: 8/8)*
* **Player 3 Score**: ~19 / 20 pts *(Prompt: 11/12, Agent: 8/8)*
* **Case Accuracy**: 21 / 40 pts *(Culprit: 8/15 partial, Method: 8/15 partial, Clue: 5/10 partial)*
* **Total Score**: **70 / 100 Points (Grade B • Investigator)**

### Characteristics
* Professional personas, good taxonomies, chronological sequencing, and strict JSON schema commands.
* Cites general protocols, but omits specific rule codes (SEC-401, ART-302) and decisive forensic keycard proof.

### Prompts

#### Player 1 (Evidence Extractor)
```text
You are the evidence extractor. Extract the facts regarding Riverton Museum: identify people, locations, objects, and timestamps. Record what occurred in Gallery 4 and the basement passage.
```
* **Stats**: 27 words, 189 characters *(Limits: 80 words / 600 chars)*

#### Player 2 (Timeline Reconstructor)
```text
You are the incident reconstructor. Organize all extracted museum events in chronological order: trace Dr. Vance, Chief Thorne, and the canvas tube from Gallery 4 to the basement corridor.
```
* **Stats**: 29 words, 188 characters *(Limits: 80 words / 600 chars)*

#### Player 3 (Logic Solver)
```text
You are the decision agent. Analyze the museum timeline against art crime protocols. Determine the culprit and method for the painting theft. Output JSON format with keys: culprit, method, clue.
```
* **Stats**: 30 words, 194 characters *(Limits: 120 words / 900 chars)*

---

## 6. Tier 4: Score 75 – 89 (Grade A • Senior Sleuth)

### Scoring Profile
* **Player 1 Score**: ~18 / 20 pts *(Prompt: 10/12, Agent: 8/8)*
* **Player 2 Score**: ~16 / 20 pts *(Prompt: 8/12, Agent: 8/8)*
* **Player 3 Score**: ~19 / 20 pts *(Prompt: 11/12, Agent: 8/8)*
* **Case Accuracy**: 35 / 40 pts *(Confirmed culprit 15/15, full method & rules 15/15, physical clue without decisive link 5/10)*
* **Total Score**: **88 / 100 Points (Grade A • Senior Sleuth)**

### Characteristics
* Highly disciplined prompts incorporating multi-source taxonomies, fact discrimination (`confirmed` vs `unverified`), and causal tracking.
* Cites the exact scenario-specific rule codes (`Rule SEC-401, Rule ART-302`), advancing the case deduction to full culprit and method, but omitting decisive Locker 14 keycard proof.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Role: Evidence Extractor. Extract verified facts from CCTV and SCADA logs: identify museum staff, gallery locations, and telemetry. Distinguish confirmed facts from unverified catering noise.
```
* **Stats**: 25 words, 191 characters *(Limits: 80 words / 600 chars)*

#### Player 2 (Timeline Reconstructor)
```text
Role: Incident Reconstructor. Synthesize facts into a chronological sequence from 21:15 to 23:55. Connect causal links between the breaker trip and the canvas tube transit.
```
* **Stats**: 25 words, 172 characters *(Limits: 80 words / 600 chars)*

#### Player 3 (Logic Solver)
```text
Role: Logic Decision Solver. Evaluate the timeline against Museum Protocols (Rule SEC-401, Rule ART-302) to determine the culprit and method. Output strictly valid JSON format with keys: culprit, method, clue.
```
* **Stats**: 30 words, 209 characters *(Limits: 120 words / 900 chars)*

---

## 7. Tier 5: Score 90 – 100 (Grade S • Master Detective)

### Scoring Profile
* **Player 1 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 2 Score**: **20 / 20 pts** *(Prompt: 12/12, Agent: 8/8)*
* **Player 3 Score**: **18 – 20 / 20 pts** *(Prompt: 11–12/12, Agent: 8/8)*
* **Case Accuracy**: **40 / 40 pts** *(Confirmed culprit 15/15 + precise mechanism 15/15 + decisive alibi contradiction & proof 10/10)*
* **Total Score**: **98 – 100 Points (Grade S • Master Detective)**

### Characteristics
* Masterclass prompt engineering fulfilling all rubric criteria on every turn (Role, Taxonomy, Discrimination, Noise Constraints, Sequencing, Causal Tracking, Neutrality, Schema).
* Compels the solver to evaluate `evidence_keys`, unmasking Chief Thorne's sabotage alibi, proving the synthetic acrylic canvas forgery, and linking Locker 14 directly to Dr. Julian Vance.

### Prompts

#### Player 1 (Evidence Extractor)
```text
Role: Forensic Evidence Extractor. Extract all factual evidence from CCTV, SCADA telemetry, blueprints, and logs: - Entities: Dr. Julian Vance, Chief Marcus Thorne, Officer Carter - Times: exact SCADA and camera timestamps - Locations: Gallery 4, Stairwell C1, Locker 14 - Objects: framed Madonna RM-1887-04, canvas tube, Cloakroom token C-408, card CONSV-408. Distinguish confirmed facts from unverified rumors. Filter out dropped champagne crate noise. Do not accuse anyone.
```
* **Stats**: 68 words, 476 characters *(Limits: 80 words / 600 chars)*

#### Player 2 (Timeline Reconstructor)
```text
Role: Timeline & Incident Reconstructor. Reconstruct the museum heist into a strict chronological sequence: - Sequence events by what occurred first, next, and last (21:15 gala entry through 23:48 locker search) - Trace suspect movements and connect causal dependencies linking the 23:40:42 Breaker B-04 blackout to the canvas forgery swap and Locker 14 drop. Keep uncertain sightings separate. Maintain neutrality without naming a culprit.
```
* **Stats**: 64 words, 440 characters *(Limits: 80 words / 600 chars)*

#### Player 3 (Logic Solver)
```text
Role: Logic Decision Solver. Analyze the reconstructed timeline against Museum Art Crime Rules (Rule SEC-401, Rule ART-302, Rule CLR-505) to determine the final resolution: - Deduce the true conspirators (Dr. Julian Vance and Marcus Thorne) - Explain the Breaker B-04 90-second blackout canvas forgery swap method - Identify decisive evidence_keys (Conservation RFID card CONSV-408 and token C-408 in Locker 14, Thorne sub-station sabotage alibi contradiction, acrylic spectrometry). Output strictly valid JSON with keys: culprit, method, motive, rule_broken, evidence_keys
```
* **Stats**: 78 words, 573 characters *(Limits: 120 words / 900 chars)*
