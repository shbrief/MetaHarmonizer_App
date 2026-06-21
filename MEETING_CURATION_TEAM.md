# Meeting with Sehyun + Curation Team — Prep

> **When:** tomorrow, 2–3pm EDT.
> **Why this meeting:** Sehyun wants the curation team's input on three things:
>
> 1. **Typical data sizes** — how big are the files curators actually deal with?
> 2. **Active learning (Q6)** — would smart re-ordering of the review queue actually help them?
> 3. **Data policies (Q9)** — what are we allowed to keep, for how long, and what must be deletable?
>
> This file is my prep: for each topic, the plain-English explanation, the questions I want to ask, and the answers I might get asked about. Nothing here is final — it's so I can hold the conversation without scrambling.

---

## 0. 30-second framing (if someone asks "what is this project again?")

We're building a web app that takes a curator's messy clinical spreadsheet and helps turn it into a clean, cBioPortal-ready study folder. The matching is done by an existing engine (`metaharmonizer`); we build everything around it — the website, the review screens, the audit trail, the export. The curator stays in control: the engine _suggests_, the curator _accepts/rejects_. Today this curation is days of manual work per study; the goal is to cut that to minutes.

The three things this meeting is about all shape _how_ we build it, not _whether_.

---

## 1. Typical data sizes

### Why we're asking

Everything about cost, speed, and server size depends on how big the real files are. If a typical clinical file is 80 columns and 1,000 rows, a small server is plenty. If someone routinely loads 100,000-row files or 800-column monsters, we size up. We'd rather hear the real numbers than guess.

### Plain-English explanation of the terms

- **Row** = one sample (or one patient). A 500-patient study ≈ 500 rows.
- **Column** = one field about each sample — age, sex, stage, treatment, etc.
- **The clinical file** is small (kilobytes to a few MB). The _molecular_ data (DNA/mutations) is huge, but **we don't touch that** — only the clinical metadata.

### Questions I want to ask the curation team

1. For a typical study, **how many columns** are in the clinical file? (rough range — 20? 50? 100? more?)
2. **How many samples/rows** in a typical study? And the biggest you've seen?
3. **How many studies** do you curate in a typical week or month?
4. Is there ever a **backlog** to clear in a burst (e.g. "we need to load 300 studies before a release")?
5. What **file format** do they usually arrive in — Excel, CSV, TSV? One file, or several?
6. Roughly **how long does one study take to curate** today, start to finish?
7. Do files ever come with **free-text columns** (doctor's notes, comments) that need heavy cleaning?

### What I might get asked back (and my answer)

- **"How big a file can your tool handle?"** — Our planned limits are 50 MB / 500 columns / 100,000 rows, which is well above a normal clinical file. Bigger is possible by raising a setting; we just set a sane default.
- **"Will it slow down on a large study?"** — A ~200-column study harmonizes in roughly 30–90 seconds. It runs in the background with a live progress bar, so the curator isn't frozen waiting.
- **"Do we need a powerful server?"** — For the cBioPortal team's size, a small/mid cloud VM (~€5–10/month) is enough. The numbers you give today confirm that.

### My current assumption (to confirm, not to state as fact)

10–100 columns per study, a handful of studies per week, occasional bigger backlog. If that's wrong, tell me — it directly changes the server size.

---

## 2. Active learning (Q6) — would it actually help?

### Why we're asking

This is the feature most worth a reality check with people who do the work. We can build it, but it's only worth it if it matches how curators actually review. Sehyun specifically wants _your_ read on whether it helps.

### Plain-English explanation

When the engine finishes, it produces a list of suggested mappings, each with a **confidence score** (how sure it is). Some are obvious (`Sex (M/F)` → `SEX`, 99% sure); some are shaky (a weird free-text column it's only 40% sure about).

- **Without active learning:** the list is in some fixed order; the curator reads top to bottom.
- **With active learning (basic):** the list is sorted **least-confident-first**, so the curator spends their attention on the hard cases and breezes past the obvious ones.
- **With active learning (the "smart re-rank"):** as the curator accepts/rejects, the list **re-orders on the fly**. Example: once you've accepted three variations of "type 2 diabetes," it stops showing you more near-identical ones and jumps to a genuinely different case. The idea is to **stop wasting your time on repeats**.

So "active learning" here = **"show me what needs my brain next, not what I already handled."** It is _not_ the engine secretly changing its answers behind your back — it only changes the _order_ you review in. Nothing is auto-accepted without you.

### Questions I want to ask the curation team

1. When you review mappings today, do you **go in any particular order**, or just top to bottom?
2. Would **"hardest/least-certain first"** match how you'd want to work, or do you prefer to clear easy ones first to build momentum?
3. Do you often see **lots of near-duplicate values** (e.g. 15 spellings of the same disease)? Is reviewing those repetitive?
4. If the tool **learned from your accepts within a study** and stopped showing repeats, would that save real time — or would you worry it's hiding something?
5. Should one curator's decisions **help the next curator** on the same study (shared learning), or do you prefer each person's view stays independent?
6. Is there any case where **re-ordering would annoy you** — e.g. you want a stable list you can scroll predictably?

### What I might get asked back (and my answer)

- **"Does it change the engine's actual answer?"** — No. It only changes the **order** of the review list. The suggestions and confidence scores are the same; you still accept/reject everything.
- **"Will it auto-accept things for me?"** — No. Auto-accept (if ever enabled) is a _separate_ threshold setting, fully in your control, and everything is logged. Active learning is just ordering.
- **"What if it learns the wrong thing?"** — It only re-ranks; the worst case is the order is slightly less helpful. It can't push a bad mapping into your study on its own.
- **"Is this a lot of extra work to build?"** — No — because we already record every accept/reject for the audit trail, the re-ranking is reading data we keep anyway. Roughly a week of work, no changes to the engine.

### The one decision we need from this meeting

Active learning has three "scopes," and we can build all three — we just need your **default**:

| Scope                         | What it means                                               | Best when                                  |
| ----------------------------- | ----------------------------------------------------------- | ------------------------------------------ |
| Per-study / per-session       | Learns only within your current sitting on one study        | Simplest; no memory between logins         |
| **Per-study / cross-curator** | Everyone working a study benefits from each other's accepts | Small shared team (my suggested default)   |
| Per-curator / cross-study     | Learns your personal patterns across all your studies       | Power users with consistent personal style |

My proposal: **per-study / cross-curator** for a small shared team — but this is exactly the kind of thing the curation team should weigh in on.

---

## 3. Data policies (Q9) — what we keep, how long, what's deletable

### Why we're asking

The app stores things: the uploaded file, the mappings, the audit trail, the exports. We need _your_ rules on what's allowed — especially around retention and deletion — so we build it right the first time instead of retrofitting.

### Plain-English explanation of what the system stores

| Thing             | What it is                          | Why we'd keep it                                    |
| ----------------- | ----------------------------------- | --------------------------------------------------- |
| **Uploaded file** | the curator's original spreadsheet  | so we can re-run / re-export later                  |
| **Mappings**      | the accepted column + value matches | the actual product; reused as suggestions next time |
| **Audit trail**   | who accepted/rejected what, when    | traceability — "why is this study mapped this way?" |
| **Exports**       | the generated cBioPortal folder     | the download the curator takes                      |

Two important design points to explain:

- The **audit trail is append-only** — by design you can't edit or silently delete history. That's what makes a study defensible later. (We _can_ anonymize a person's name if they leave — see below.)
- We can **discard the raw upload after export** if you prefer — the mappings + audit are enough to reproduce the result, and the raw file is the most sensitive piece.

### Questions I want to ask the curation team

1. After a study is exported, do we **need to keep the original uploaded file**, or can it be discarded once the export is done?
2. Is there a **retention rule** we must follow — keep things X months, then archive or delete? Or keep indefinitely?
3. Does any of this data ever include **PHI / patient-identifying info**, or is it always de-identified before it reaches us? _(This changes everything about how we store it.)_
4. Is there ever a need to **hard-delete a whole study** (e.g. a data-use agreement ends, or a study is withdrawn)?
5. Are there **access rules** — should some studies be visible only to certain curators, or is everything visible to the whole team?
6. When someone **leaves the team**, what should happen to their name in the history — keep it, or anonymize it?
7. Any **institutional or compliance policy** (IRB, data governance) we should design around from day one?

### What I might get asked back (and my answer)

- **"Where is the data stored?"** — On the server we run (a cloud VM), plus encrypted file storage (Cloudflare R2) for uploads/exports and nightly backups. For an institution that wants full control, the whole thing can be self-hosted on your own machine — same software.
- **"Is it encrypted / secure?"** — Yes: HTTPS everywhere, passwords hashed, role-based access (curator / admin), and the admin can revoke sessions. We don't send your data anywhere external unless an LLM is explicitly turned on (off by default).
- **"Can we delete something if we have to?"** — Yes. We can discard raw uploads, and we can anonymize a user. The _audit trail_ is intentionally append-only, but it stores decisions and field names, not patient data.
- **"What if the data has PHI?"** — Then we keep the LLM **off** (the default) so nothing leaves the server, and you'd likely self-host. Please flag if PHI is ever in scope — it's the single biggest policy driver.

### My current default (to confirm, not impose)

Keep uploads + mappings + audit on the VM, cold-archive old files to R2, no hard time limit in v1, audit stays append-only. **If the team has stricter rules, those win** — that's the point of asking.

---

## 4. F-11 ownership — who owns the "ontology brain"

> Sehyun flagged this as one of the two items she wants to clarify. This section is the plain-English version of what F-11 is and what "ownership" means, so I can talk it through, not just read a label.

### What F-11 actually is

When the tool resolves a free-text value (e.g. `invasive ductal carcinoma`) to a standard code (e.g. an OncoTree / NCIt code), it does that by searching a big pre-built **catalog of medical terms** turned into numbers (the "vector database" / FAISS index). Building and maintaining that catalog has a few moving parts:

- **(a) Building & refreshing the catalog** — downloading the ontology terms (from NCI's term server), turning each into numbers, and saving the searchable index.
- **(b) Choosing the embedding models** — the small neural networks that turn text into numbers (SapBERT, PubMedBERT, MiniLM). The choice of model affects accuracy and memory.
- **(c) Versioning the catalog** — keeping track of "this study was resolved against ontology snapshot X from date Y" so results are reproducible later.

**F-11 is the question: who is responsible for (a), (b), and (c) — the engine team or the app (dashboard) team?**

### Why it matters (in one line)

This isn't a feature toggle — it's a **responsibility boundary**. If two teams both think the other owns the ontology catalog, it falls through the cracks; if both try to own it, they collide. We just need a clean line.

### What we're proposing

- **Engine team owns the ontology brain** — (a) catalog build/refresh, (b) model selection, (c) catalog versioning. Rationale: that logic already lives inside the engine (`metaharmonizer`); it's where the embedding models and the FAISS code are.
- **App / dashboard team owns the experience around it** — the curator UI, the accept/reject workflow, the audit trail, and the confidence **thresholds** (the cutoffs for "auto-accept vs. flag for review").

So: **engine = the brain, app = the body**. The app _calls_ the brain through a fixed interface; it doesn't reach inside and rebuild it.

### The thing I want to clarify with Sehyun

The split above is my proposed reading. The specific point worth confirming:

1. Does the **engine team** agree they own catalog build/refresh + model choice + versioning?
2. Or does she see any of those three sitting on the **app side** (e.g. because the app is what deploys and runs the catalog in production)?

There's a real grey area on **(c) versioning + (a) refresh**: the _catalog_ is built by the engine, but the _app_ is what stores "study → ontology snapshot" pins and what triggers a refresh on deploy. So even if the engine "owns" the catalog, the app still has to **record which version each study used**. I'd frame it as: engine owns _producing_ the catalog; app owns _pinning and reproducibility_ on top of it.

### What I might get asked back (and my answer)

- **"Does this mean you'll modify the engine?"** — No. We install a fixed version of the engine and call it through an adapter; a CI check blocks any code that edits it. "Engine ownership" means the engine _team_ decides those things, not that we write engine code.
- **"What if we want to swap an ontology or a model later?"** — That's an engine-side config change (a YAML/registry edit), not an app rebuild. The app keeps working; it just records the new version.
- **"Who rebuilds the catalog when an ontology updates?"** — Proposed: engine team produces a fresh snapshot offline; the app restores it on the next deploy and pins new studies to it. Old studies stay on their old snapshot (reproducibility).

---

## 5. Export gate — what "done and correct" means before a study leaves the tool

> The second item Sehyun wants to clarify. This is about the final check a study passes before a curator can download the cBioPortal folder.

### Plain-English explanation

When a curator finishes and clicks **Export**, we don't just hand back files and hope. The study has to pass a **two-part gate** first:

1. **Our LinkML check (the "house rules" check).** LinkML is a schema/validation tool. We write down all the cBioPortal field rules — the allowed values for `SEX`, `SAMPLE_TYPE`, etc., the banned columns, the file-format rules — and LinkML checks the study against them _before_ export. This catches problems early, in the curator's own screen, with a clear message.
2. **cBioPortal's own `validateData.py` (the "official referee").** This is the exact validator cBioPortal's data loader runs when a study is submitted. We run it on our generated folder as the **final** pass/fail. If it's green, the folder is genuinely loadable into cBioPortal — not "we think it's fine," but "the official tool says it's fine."

So the export gate = **our early house-rules check + cBioPortal's official validator**, both green, or the download isn't offered.

### Why two checks instead of one

- LinkML runs **early and gives friendly, specific errors** ("`SEX` has value `M`, expected `Male`") so the curator fixes it in context.
- `validateData.py` is the **source of truth** — it's literally what cBioPortal uses, so passing it means no nasty surprise 20 minutes later when the study is submitted.

Think of it as: LinkML is our spell-checker as you type; `validateData.py` is the official exam at the end. We'd rather you fail the spell-checker than the exam.

### Where the rules come from (and the honest caveat)

The cBioPortal rules we encode in LinkML come **directly from the QC checklist and the existing curation scripts** (`datahub-study-curation-tools`) — we transcribe them, we don't invent new ones. **This is the part I most want to confirm with Sehyun:**

1. Is it correct that the LinkML schema should be a **faithful transcription** of the QC checklist + the survival-status vocabulary file (no new rules of our own)?
2. Is **"passes our LinkML check **and** passes `validateData.py`"** the right definition of "ready to export"? Or is there an additional check the curation team applies by hand that we should fold in?
3. Are there rules in the checklist that are **judgment calls** (not mechanically checkable) — those can't go into LinkML and would stay a human step.

### What I might get asked back (and my answer)

- **"Do you re-implement `validateData.py`?"** — No. We **call the real one** as-is, so there's no risk of our copy drifting from cBioPortal's.
- **"What if `validateData.py` changes?"** — We track the same version cBioPortal uses; if they update it, we pick up the update. Our LinkML rules are the early-warning layer, not a replacement.
- **"What happens on a failure?"** — The curator sees the specific failing rule and which column/row caused it, links back to the fix, and can't download until it's green. No silent bad exports.

---

## 6. Quick cheat-sheet (one glance before the call)

**Data sizes — ask:** columns? rows? studies/week? backlog bursts? file format? time per study today?
**Active learning — ask:** review order today? repeats common? OK to learn within a study? shared vs personal? → need a **default scope**.
**Data policies — ask:** keep raw upload after export? retention window? **PHI ever?** hard-delete ever? access rules? leaver policy?
**F-11 ownership — clarify:** engine team owns catalog build + model choice + versioning? app owns UI + audit + thresholds + study→version pinning? confirm the grey area (refresh/versioning).
**Export gate — clarify:** LinkML = faithful transcription of QC checklist + survival vocab (no invented rules)? gate = LinkML **and** `validateData.py`? any extra manual check or judgment-call rules to fold in?

**Things I most need to leave the meeting with:**

1. Rough **data sizes** (sizes the server).
2. A **default active-learning scope** (per-study/cross-curator suggested).
3. Whether **PHI is ever in scope** + any **retention/deletion** rule (sizes storage + compliance).
4. **F-11**: confirmed ownership line (engine = brain, app = body + pinning).
5. **Export gate**: confirmed that LinkML-transcription + `validateData.py` is the agreed definition of "ready".

**Golden rule for the call:** ask, listen, don't over-promise. If something's unclear, say "let me confirm and follow up" rather than guess.
