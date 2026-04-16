"""
LLM-as-Judge Quality Evaluation for Workspace Comparison
=========================================================
Performs blind, randomized evaluation of answer pairs from
tools/comparison_report_graph.md using a multi-dimensional rubric.

Each answer pair is shuffled so the judge doesn't know which workspace
produced which answer. Evaluation dimensions:

  1. Accuracy        - Factual correctness, proper references
  2. Completeness    - Coverage of all relevant aspects
  3. Specificity     - Concrete details vs vague generalizations
  4. Structure       - Organization, tables, traceability
  5. Actionability   - Usefulness for proposal writing team

Usage:
    python tools/evaluate_quality.py
    python tools/evaluate_quality.py --report tools/comparison_report_graph.md
    python tools/evaluate_quality.py --output tools/quality_evaluation.md
"""

from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import json
import logging
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate_quality")

# ─── Constants ────────────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an expert government contracting (GovCon) proposal analyst evaluating RAG system answer quality. You will receive a question about a federal RFP document and two answers labeled "Answer 1" and "Answer 2". You do NOT know which system produced which answer.

Evaluate each answer on these 5 dimensions using a 1-5 scale:

**1. Accuracy (1-5)**: Are the facts correct? Are FAR/DFARS references accurate? Are document section numbers, CDRL numbers, page limits, and evaluation criteria stated correctly? Deduct for hallucinated or incorrect details.

**2. Completeness (1-5)**: Does the answer cover ALL relevant aspects of the question? Are there gaps where important information is missing? Does it address edge cases or secondary requirements?

**3. Specificity (1-5)**: Does the answer provide concrete details (section numbers, exact thresholds, specific CDRL identifiers, named personnel types, dollar amounts) rather than vague generalizations?

**4. Structure (1-5)**: Is the answer well-organized with clear headings, tables where appropriate, logical flow, and easy traceability back to source documents?

**5. Actionability (1-5)**: Could a proposal team USE this answer directly for compliance matrix creation, proposal writing, or bid/no-bid decisions? Does it provide strategic insight beyond mere recitation?

For each dimension, provide:
- Score for Answer 1 (1-5)
- Score for Answer 2 (1-5)
- Brief justification (1-2 sentences)

Then provide an OVERALL WINNER determination with reasoning.

Respond ONLY in this exact JSON format:
{
  "accuracy": {"answer_1": <int>, "answer_2": <int>, "justification": "<text>"},
  "completeness": {"answer_1": <int>, "answer_2": <int>, "justification": "<text>"},
  "specificity": {"answer_1": <int>, "answer_2": <int>, "justification": "<text>"},
  "structure": {"answer_1": <int>, "answer_2": <int>, "justification": "<text>"},
  "actionability": {"answer_1": <int>, "answer_2": <int>, "justification": "<text>"},
  "overall_winner": "answer_1" | "answer_2" | "tie",
  "overall_reasoning": "<text>",
  "confidence": "high" | "medium" | "low"
}"""

DIMENSIONS = ["accuracy", "completeness", "specificity", "structure", "actionability"]


# ─── Report parser ────────────────────────────────────────────────────────────

def parse_report(report_path: Path) -> list[dict]:
    """Parse comparison report into structured question/answer pairs."""
    text = report_path.read_text(encoding="utf-8")

    # Split on ## Q\d+ headers
    question_blocks = re.split(r"(?=^## Q\d+:)", text, flags=re.MULTILINE)
    question_blocks = [b for b in question_blocks if b.strip().startswith("## Q")]

    results = []
    for block in question_blocks:
        # Extract question ID and category
        header_match = re.match(r"## (Q\d+): (.+)", block)
        if not header_match:
            continue
        qid = header_match.group(1)
        category = header_match.group(2).strip()

        # Extract mode and query text
        mode_match = re.search(r"\*\*Query \((\w+) mode\):\*\*\s*(.+?)(?:\n|$)", block)
        mode = mode_match.group(1) if mode_match else "unknown"
        query = mode_match.group(2).strip() if mode_match else ""

        # Split into workspace answers using ### afcapv headers
        ws_splits = re.split(r"(?=^### afcapv)", block, flags=re.MULTILINE)
        answers = {}
        for ws_block in ws_splits:
            ws_match = re.match(r"### (afcapv_bos_i_t\d+)", ws_block)
            if ws_match:
                ws_name = ws_match.group(1)
                # Remove the header and response time line
                content = re.sub(r"^### afcapv_bos_i_t\d+\s*\n", "", ws_block)
                content = re.sub(r"\n\*Response time:.*?\*\s*$", "", content, flags=re.DOTALL)
                content = re.sub(r"\n---\s*$", "", content)
                # Remove trailing reference sections from next question
                content = content.strip()
                answers[ws_name] = content

        if len(answers) == 2:
            ws_names = sorted(answers.keys())
            results.append({
                "id": qid,
                "category": category,
                "mode": mode,
                "query": query,
                "ws_a_name": ws_names[0],
                "ws_a_answer": answers[ws_names[0]],
                "ws_b_name": ws_names[1],
                "ws_b_answer": answers[ws_names[1]],
            })

    return results


# ─── LLM judge ────────────────────────────────────────────────────────────────

async def judge_answer_pair(query: str, answer_a: str, answer_b: str, qid: str) -> dict:
    """Send a blinded answer pair to the LLM for evaluation."""
    # Randomly shuffle to eliminate position bias
    coin = random.random() > 0.5
    if coin:
        ans1, ans2 = answer_a, answer_b
        mapping = {"answer_1": "a", "answer_2": "b"}
    else:
        ans1, ans2 = answer_b, answer_a
        mapping = {"answer_1": "b", "answer_2": "a"}

    user_prompt = f"""## Question
{query}

## Answer 1
{ans1}

## Answer 2
{ans2}

Evaluate both answers using the rubric. Respond ONLY with valid JSON."""

    api_key = os.environ.get("LLM_BINDING_API_KEY", "")
    base_url = os.environ.get("LLM_BINDING_HOST", "https://api.x.ai/v1")
    model = os.environ.get("REASONING_LLM_NAME", os.environ.get("LLM_MODEL", "grok-4-1-fast-reasoning"))

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent evaluation
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)
        # Also try direct parse
        result = json.loads(raw)

        # De-blind: map back answer_1/answer_2 to workspace a/b
        result["_mapping"] = mapping
        result["_shuffled"] = coin
        return result

    except json.JSONDecodeError:
        logger.error(f"[{qid}] Failed to parse LLM judge response as JSON")
        logger.debug(f"Raw response: {raw[:500]}")
        return {"_error": "json_parse_failure", "_raw": raw[:500], "_mapping": mapping}
    except Exception as e:
        logger.error(f"[{qid}] LLM judge call failed: {e}")
        return {"_error": str(e), "_mapping": mapping}


# ─── Evaluation runner ────────────────────────────────────────────────────────

async def run_evaluation(questions: list[dict]) -> list[dict]:
    """Run sequential blind evaluation on all question pairs."""
    results = []
    for q in questions:
        qid = q["id"]
        print(f"  [{qid}] Evaluating ({q['category']}, {q['mode']})...", end="", flush=True)
        t0 = time.time()

        judgment = await judge_answer_pair(
            query=q["query"],
            answer_a=q["ws_a_answer"],
            answer_b=q["ws_b_answer"],
            qid=qid,
        )

        elapsed = time.time() - t0
        print(f" done ({elapsed:.1f}s)")

        results.append({
            **q,
            "judgment": judgment,
        })

    return results


# ─── Report writer ────────────────────────────────────────────────────────────

def deblind_scores(judgment: dict) -> dict:
    """Convert blinded answer_1/answer_2 scores back to workspace a/b."""
    mapping = judgment.get("_mapping", {"answer_1": "a", "answer_2": "b"})
    deblined = {}
    for dim in DIMENSIONS:
        if dim in judgment:
            scores = judgment[dim]
            deblined[dim] = {
                "ws_a": scores.get(f"answer_{1 if mapping['answer_1'] == 'a' else 2}", 0),
                "ws_b": scores.get(f"answer_{1 if mapping['answer_1'] == 'b' else 2}", 0),
                "justification": scores.get("justification", ""),
            }
    # Deblind overall winner
    raw_winner = judgment.get("overall_winner", "tie")
    if raw_winner == "tie":
        deblined["winner"] = "tie"
    elif raw_winner in mapping:
        ws_letter = mapping[raw_winner]
        deblined["winner"] = f"ws_{ws_letter}"
    else:
        deblined["winner"] = "tie"
    deblined["overall_reasoning"] = judgment.get("overall_reasoning", "")
    deblined["confidence"] = judgment.get("confidence", "unknown")
    return deblined


def write_evaluation_report(results: list[dict], output_path: Path):
    """Write detailed evaluation report in Markdown."""
    lines = [
        "# Quality Evaluation Report (LLM-as-Judge, Blind)",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Judge Model:** {os.environ.get('LLM_MODEL', 'unknown')}",
        f"**Temperature:** 0.1 (deterministic judging)",
        f"**Evaluation Method:** Randomized blind pairing (position bias eliminated)",
        "",
    ]

    # Aggregate scores
    ws_a_total = {d: 0 for d in DIMENSIONS}
    ws_b_total = {d: 0 for d in DIMENSIONS}
    ws_a_wins = 0
    ws_b_wins = 0
    ties = 0
    valid_count = 0

    # Executive summary table
    lines += [
        "## Executive Summary",
        "",
        "| Q | Category | Mode | Winner | Confidence | A Score | B Score | Delta |",
        "|:--|:---------|:-----|:------:|:----------:|:-------:|:-------:|:-----:|",
    ]

    for r in results:
        j = r["judgment"]
        if "_error" in j:
            lines.append(f"| {r['id']} | {r['category']} | `{r['mode']}` | ERROR | - | - | - | - |")
            continue

        deblined = deblind_scores(j)
        a_score = sum(deblined[d]["ws_a"] for d in DIMENSIONS if d in deblined)
        b_score = sum(deblined[d]["ws_b"] for d in DIMENSIONS if d in deblined)
        delta = b_score - a_score

        winner_label = deblined["winner"].replace("ws_a", "t4").replace("ws_b", "t5")
        if winner_label == "tie":
            winner_label = "TIE"
            ties += 1
        elif "t4" in winner_label:
            ws_a_wins += 1
        else:
            ws_b_wins += 1

        conf = deblined.get("confidence", "?")
        sign = "+" if delta > 0 else ""
        lines.append(
            f"| {r['id']} | {r['category']} | `{r['mode']}` | **{winner_label}** | {conf} | {a_score}/25 | {b_score}/25 | {sign}{delta} |"
        )

        # Accumulate per-dimension totals
        for d in DIMENSIONS:
            if d in deblined:
                ws_a_total[d] += deblined[d]["ws_a"]
                ws_b_total[d] += deblined[d]["ws_b"]
        valid_count += 1

    lines += [
        "",
        f"**Overall: t4 wins {ws_a_wins}, t5 wins {ws_b_wins}, ties {ties}** (out of {valid_count} evaluated)",
        "",
    ]

    # Per-dimension aggregates
    if valid_count > 0:
        lines += [
            "## Dimension Breakdown (Aggregate)",
            "",
            "| Dimension | t4 Total | t5 Total | t4 Avg | t5 Avg | Better |",
            "|:----------|:--------:|:--------:|:------:|:------:|:------:|",
        ]
        for d in DIMENSIONS:
            a_t = ws_a_total[d]
            b_t = ws_b_total[d]
            a_avg = a_t / valid_count
            b_avg = b_t / valid_count
            better = "t4" if a_t > b_t else ("t5" if b_t > a_t else "TIE")
            lines.append(
                f"| {d.capitalize()} | {a_t}/{valid_count*5} | {b_t}/{valid_count*5} | {a_avg:.1f} | {b_avg:.1f} | **{better}** |"
            )

        # Grand total
        a_grand = sum(ws_a_total.values())
        b_grand = sum(ws_b_total.values())
        lines += [
            "",
            f"**Grand Total: t4 = {a_grand}/{valid_count*25}, t5 = {b_grand}/{valid_count*25}**",
            "",
        ]

    # Detailed per-question analysis
    lines += ["---", "", "## Detailed Per-Question Analysis", ""]

    for r in results:
        j = r["judgment"]
        lines += [f"### {r['id']}: {r['category']} (`{r['mode']}` mode)", ""]
        lines += [f"**Query:** {r['query']}", ""]

        if "_error" in j:
            lines += [f"> **ERROR:** {j['_error']}", ""]
            continue

        deblined = deblind_scores(j)
        was_shuffled = j.get("_shuffled", "?")
        lines += [f"*Position randomization applied: {was_shuffled}*", ""]

        lines += [
            "| Dimension | t4 | t5 | Justification |",
            "|:----------|:--:|:--:|:--------------|",
        ]
        for d in DIMENSIONS:
            if d in deblined:
                dd = deblined[d]
                lines.append(f"| {d.capitalize()} | {dd['ws_a']} | {dd['ws_b']} | {dd['justification']} |")

        a_total = sum(deblined[d]["ws_a"] for d in DIMENSIONS if d in deblined)
        b_total = sum(deblined[d]["ws_b"] for d in DIMENSIONS if d in deblined)
        winner = deblined["winner"].replace("ws_a", "t4").replace("ws_b", "t5")
        if winner == "tie":
            winner = "TIE"

        lines += [
            "",
            f"**Total: t4={a_total}/25, t5={b_total}/25 → Winner: {winner}** ({deblined.get('confidence', '?')} confidence)",
            "",
            f"> {deblined.get('overall_reasoning', 'No reasoning provided.')}",
            "",
        ]

    # Methodology note
    lines += [
        "---",
        "",
        "## Methodology",
        "",
        "- **Blind evaluation**: Answer pairs randomly shuffled before presentation to judge LLM",
        "- **No length bias**: Rubric scores content quality, not quantity",
        "- **Domain-specific rubric**: Scoring criteria designed for government contracting RFP analysis",
        "- **Low temperature (0.1)**: Minimizes random variation in scoring",
        "- **5 dimensions × 5-point scale**: 25 points maximum per answer per query",
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Evaluation report saved: {output_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LLM-as-Judge Quality Evaluation")
    parser.add_argument(
        "--report",
        type=str,
        default="tools/comparison_report_graph.md",
        help="Path to comparison report to evaluate",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tools/quality_evaluation.md",
        help="Path for evaluation output report",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible shuffling",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    output_path = Path(args.output)

    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}")
        sys.exit(1)

    random.seed(args.seed)

    print(f"Parsing report: {report_path}")
    questions = parse_report(report_path)
    print(f"Found {len(questions)} question pairs to evaluate")

    if not questions:
        print("ERROR: No question pairs found in report")
        sys.exit(1)

    for q in questions:
        print(f"  {q['id']}: {q['category']} ({q['mode']}) - A={len(q['ws_a_answer'])} chars, B={len(q['ws_b_answer'])} chars")

    print(f"\nRunning blind LLM evaluation...")
    results = asyncio.run(run_evaluation(questions))

    print(f"\nWriting evaluation report...")
    write_evaluation_report(results, output_path)

    # Print quick summary
    wins_a = sum(1 for r in results if "_error" not in r["judgment"] and deblind_scores(r["judgment"]).get("winner") == "ws_a")
    wins_b = sum(1 for r in results if "_error" not in r["judgment"] and deblind_scores(r["judgment"]).get("winner") == "ws_b")
    ties_count = sum(1 for r in results if "_error" not in r["judgment"] and deblind_scores(r["judgment"]).get("winner") == "tie")
    print(f"\n  RESULT: t4 wins {wins_a}, t5 wins {wins_b}, ties {ties_count}")


if __name__ == "__main__":
    main()
