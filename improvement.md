# Improvement beyond the brief: the pre-meeting health check

## The problem it solves

The brief asks for an analysis Adjoa can rerun every quarter, on her own laptop, sometimes live in a meeting, and without me. Rerunning the code is the easy part. The hard part is knowing **whether the new run can be trusted, and what changed**, before she says anything in the room.

This year's data shows how much can go wrong without anything crashing. Eight rows could not be assessed. Seven were repeats. Ten of 23 bundles were missing films. And the verdict depends on just 12 post-2000 standalones. Next year's list will be four times larger, assembled the same way. Every one of these problems produces a confident-looking answer. Without a check, Adjoa finds out what changed when someone in the meeting asks. That is the scenario Kwame fears most: hearing it from Finance in November rather than from his own team in October.

The decision notes record that "a new kind of problem needs a person to spot it". The health check tells that person where to look.

## What I built

`src/health_check.py`: one command, `.venv\Scripts\python src\health_check.py`. It reruns the whole analysis, then writes `reports/health_check.md`, a one-page traffic-light report:

| Part | What it checks | Why it matters to Kwame |
|---|---|---|
| Trust checks | All rows accounted for; downloads complete; share of unusable rows; repeats; films without credible money figures; size of the post-2000 standalone sample; bundles missing films; age of the data; whether the two periods agree | Each one is a finding from this year's data diagnosis, turned into a rule with a threshold and a plain-English "what to do" |
| Change checks | Compared with the last run Kwame saw: verdicts, score gap, strongest bundle, and which picks came in or went out | No surprises in the room: Adjoa can explain every change before anyone asks |
| Overall grade | 🔴 **RED**: do not present. 🟠 **AMBER**: present, but say these items out loud. 🟢 **GREEN**: safe. | One glance before walking in |

After reviewing a run, Adjoa marks it as the new reference with `--accept` (a RED run cannot be accepted). The command returns an error code on RED, so it could also gate any future automation.

**Tested on a simulated next quarter.** I removed *The Lord of the Rings* and *Pulp Fiction* from the list and added two junk rows. The check:
- flagged the two new unusable rows (10 instead of 8)
- reported the strongest bundle changing from *Lord of the Rings* to *The Avengers*
- named every pick that left (*Lord of the Rings*, *Pulp Fiction*) and every pick that arrived (*The Dark Knight*, *Interstellar*)
- caught that the post-2000 verdict moved from "too close to call" to "standalone"

All of these would have changed what Kwame says to the board.

**It also found a real defect in my own pipeline before anyone else could.** The table builder was reading *every* saved reply on disk, not just the films on the current list. On a new list, films from old lists would have leaked into the analysis. The built-in join check stopped the run rather than give a wrong answer. I fixed the builder to read only the current list's films, re-confirmed that this year's results are unchanged, and re-measured speed: it is slightly faster now.

On this year's data the overall grade is **AMBER**. The amber items (unusable rows, the small post-2000 standalone sample, incomplete bundles, and the answer changing between periods) are exactly the caveats in the memo.

## What it is worth to Kwame

- **No surprises at the board.** Every change since the last presentation is listed before the meeting, with what to say about it. A pick dropping out or a verdict flipping is the kind of thing Finance would otherwise discover for him.
- **Adjoa can run it without me.** The judgement I applied this year (which problems matter and when to worry) is written down as rules with thresholds, not kept in my head. She does not need to reread every decision note before each quarter. The report tells her which ones are relevant.
- **Protection against a wrong answer that doesn't crash.** It turns "the code ran" into "the code ran *and* the result is fit to present". This matters more as the list grows to 500 titles assembled from the same three kinds of source.
- **A record over time.** The accepted reference shows what Kwame was told and when, which is useful when the board asks "what did we know last quarter?"

## What it cost

- **Build:** about 200 lines of code that reuse the existing pipeline and outputs, so there is no second copy of the analysis to keep in sync. Testing on a simulated list took one additional run.
- **Each use:** 2.2 seconds measured, the same as a normal rerun. It makes no extra requests to the shared film database.
- **Upkeep:** the thresholds are judgement calls, set from this year's data: 5% / 15% unusable rows, 30 / 10 post-2000 standalones, 25% incomplete bundles, 100-day-old data, and a 5-point score-gap move. They are named at the top of the file. After a year of quarterly runs, Adjoa should tune them to what actually proved worth raising.
- **Limit:** it can only check for problems someone has already thought of. A brand-new kind of data problem still needs a person, but the change report makes its effects visible.
