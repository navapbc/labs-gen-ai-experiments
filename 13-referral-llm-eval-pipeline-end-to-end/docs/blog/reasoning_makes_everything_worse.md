# Reasoning makes everything worse

**Draft — technical eval insight post #2**
*Based on: experiment 13 standalone reasoning-quality study (April 2026). Raw data and report in [`docs/analysis/reasoning_quality_report.md`](../analysis/reasoning_quality_report.md).*

---

When OpenAI added `reasoning.effort` to the Responses API, the default instinct was: more reasoning = better answers. That's how most humans work, and the parameter names — `none`, `low`, `medium`, `high` — practically dare you to crank it up.

For our referral tool, we cranked it up. It made everything worse.

## What we tested

We run an LLM-powered referral tool: caseworkers describe a client's needs, the model returns a JSON list of local resources — food pantries, shelters, legal aid, employment programs, clinics. Real people get these referrals. Wrong phone numbers waste their time; closed programs send them to empty buildings.

Our production config is `gpt-5.1`, `reasoning="none"`, `temperature=0.5`. We wanted to know: would turning reasoning up make the output better?

So we ran the experiment:

- 20 real caseworker queries, pulled from Phoenix (our LLM tracing platform), with the full production RAG context preserved
- 4 reasoning levels: `none`, `low`, `medium`, `high`
- Same model (`gpt-5.1`), same prompt (our production v53), everything else held constant
- Each output scored across 7 quality dimensions we'd already validated: JSON structure, resource count, URL validity, duplicates, readability, contact completeness, and RAG grounding
- Randomized order, per-call hard timeout, checkpoint every 10 calls

The design was a clean factorial. The only variable was reasoning effort.

## What we found

Three findings, all monotonic in reasoning level:

| Level   | Avg quality flags | Avg latency | Web-search rate | Completion rate |
|---------|------------------:|------------:|----------------:|----------------:|
| none    | **1.71** | **16s**  | 65%  | 85% |
| low     | 1.83     | 28s      | 83%  | 90% |
| medium  | 2.00     | 96s      | 88%  | 40% |
| high    | 2.86     | 252s     | 100% | 35% |

**Quality got worse.** Average quality flags climbed from 1.71 (none) to 2.86 (high) — a 67% increase in detected issues. In head-to-head matchups on the same query, `reasoning="none"` won or tied every comparison against every other level. Not once did a higher reasoning level produce a measurably better output.

**Latency exploded.** Responses at `high` took 16x longer than at `none` — a 252-second median vs. 16. Web-search rate climbed from 65% to 100% as reasoning increased, explaining some of the slowdown, but not all of it. The model was thinking harder *and* searching more, and both were slower, and neither helped.

**Reliability collapsed.** This is the finding that surprised us most. `reasoning="medium"` and `reasoning="high"` hung past our 180-second timeout on more than half of queries — requiring us to kill the process and restart. We tried three separate runs. Same pattern every time: either the call would complete in 90–400 seconds, or it would hang indefinitely. With production-length prompts (~15,000 characters of RAG context), higher reasoning levels didn't just take longer — they regularly stopped responding at all.

## Why it happens

The best explanation we have — and it's a hypothesis, not a proven mechanism — is that reasoning models are optimized for problems with a hidden chain of logic. Math, code reasoning, multi-step planning. For those, thinking longer really does help.

Our task isn't that. It's closer to retrieval and formatting: "given this list of resources and this client need, pick the relevant ones and return JSON with the right fields." There's no hidden chain of reasoning to uncover. When you force the model to "think" about it, it starts second-guessing, triggers unnecessary web searches, and produces more verbose (more flag-prone) outputs.

You can see this in the web-search numbers. At `reasoning="none"`, the model used web search on 65% of queries — only when it seemed actually needed. At `reasoning="high"`, it used web search 100% of the time. That's not more thoughtful. That's a model that has been told to think harder, deciding that "think harder" means "do more stuff."

## What we shipped

We stayed on `reasoning="none"`. That's our production config today, and the data says it should stay that way.

More broadly: for any LLM task that's primarily **structured output over provided context** — retrieval, formatting, classification, tagging, extraction — default to `reasoning="none"` and don't move until you have a measured reason to. The parameter isn't a free quality dial. At best it's a no-op. At worst, for tasks like ours, it makes every axis you care about measurably worse.

## When reasoning might actually help

We didn't test this, so take it as an educated guess: reasoning probably earns its cost on tasks where the model has to *derive* something that isn't present in the input. Multi-step math. Code debugging. Planning under constraints. Novel puzzles. Things where "think for another 30 seconds" plausibly produces a better answer than the first-pass response.

For everything in the "find the right thing in the provided context and format it correctly" shape — which is most LLM product features in 2026 — our strong prior now is that reasoning is a trap. Measure it in your own pipeline before you turn it on.

## The broader point

It's tempting to treat new model parameters as unambiguous upgrades: "reasoning=high means the model thinks more, thinking more is good, done." That's not how any of this works. Every parameter is a tradeoff, and the only way to know which side of the tradeoff you're on is to run the experiment on your actual task, with your actual data.

We got lucky that this one was easy to test — same model, same prompt, one variable. Most of our parameter decisions aren't that clean. But even a scrappy 50-call experiment with production queries gave us a definitive answer on one parameter and saved us from a 16x latency regression.

If you've been leaving `reasoning.effort` on its default and wondering whether you should turn it up: don't. Run the experiment first.

---

*Methodology note: 20 queries × 4 levels = 80 planned calls. We completed 50 across three runs; the 30 that didn't complete all hung at `reasoning="medium"` or `"high"` past the 180-second timeout. Excluding those would flatter the higher-reasoning numbers, not hurt them — the reliability finding is real, not an artifact of the timeout. Full per-call results, pairwise win rates, and dimension-by-dimension breakdown are in [the report](../analysis/reasoning_quality_report.md).*
