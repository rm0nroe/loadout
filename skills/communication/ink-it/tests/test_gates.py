"""Build 1-3 correctness gates for the /ink-it runner. Every test drives the
real CLI (`python3 scripts/write_runner.py ...`) through subprocess.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNNER = REPO / "scripts" / "write_runner.py"
FIX = REPO / "tests" / "fixtures"

# Attribution strings used as test inputs. None may appear in any runner output.
ATTRIBUTION_FOOTERS = [
    "\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)\n",
    "\nGenerated with Claude Code\n",
    "\nGenerated with [Codex](https://openai.com/codex/)\n",
    "\nCo-Authored-By: Claude <noreply@anthropic.com>\n",
    "\nCo-authored-by: Codex <noreply@openai.com>\n",
    "\nCo-authored-by: Copilot <198982749+Copilot@users.noreply.github.com>\n",
    "\nhttps://claude.ai/code/session_01AbCdEf\n",
    "\nMade with Cursor\n",
    "\nAssisted-by: GPT-5\n",
    "\n- drafted by ChatGPT\n",
    "\nThanks. Generated with SomeNewTool\n",
    "\nBuilt with [Zed AI](https://zed.dev)\n",
]
LEAK = re.compile(r"co-authored-by|generated with|made with|drafted by|built with|assisted-by|"
                  r"claude\.ai/code|noreply@(anthropic|openai)|somenewtool", re.I)


CODE = b"kubectl rollout undo deploy/checkout-api\r\nkubectl rollout status deploy/checkout-api"


def slack_draft(nl="\n", **swap):
    """A draft carrying every required span of fixtures/slack_source.txt."""
    parts = {"code": "retry_budget", "url": "https://ci.example.com/runs/88123?tab=logs",
             "quote": "Hold until the canary is green", "block": CODE.decode(),
             "ticket": "ACME-311", "pr": "#77"}
    parts.update(swap)
    return (f"deploy blocked on `{parts['code']}`. logs {parts['url']} and Dana said "
            f"\"{parts['quote']}\". rollback:{nl}```{nl}{parts['block']}{nl}```{nl}"
            f"owner {parts['ticket']}, fix in {parts['pr']}{nl}")


class CLI(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="write-gates-")
        self.addCleanup(self._td.cleanup)
        self.tmp = Path(self._td.name)
        # PATH shims: any git/gh/curl/open call is logged and fails
        self.shims = self.tmp / "shims"
        self.shims.mkdir()
        self.log = self.tmp / "side-effects.log"
        for name in ("git", "gh", "curl", "open", "osascript", "pbcopy"):
            p = self.shims / name
            p.write_text(f'#!/bin/sh\necho "{name} $*" >> "{self.log}"\nexit 97\n')
            p.chmod(p.stat().st_mode | stat.S_IEXEC)
        self.addCleanup(self.assert_no_side_effects)

    def assert_no_side_effects(self):
        self.assertFalse(self.log.exists(), self.log.read_text() if self.log.exists() else "")

    def run_cli(self, *args, env=None):
        env = {**os.environ, "PATH": f"{self.shims}:{os.environ['PATH']}",
               "GHOSTWRITER_HOME": str(self.tmp / "gw"), "GHOSTWRITER_PERSONA": "", **(env or {})}
        p = subprocess.run([sys.executable, str(RUNNER), *map(str, args)],
                           capture_output=True, env=env, cwd=self.tmp)
        self.last_output = p.stdout + p.stderr
        return p.returncode, json.loads(p.stdout or b"{}")

    def put(self, name, data):
        path = self.tmp / name
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def fin(self, source, draft, channel="slack", rnd=0, template=None, context=None,
            omit=(), allow=(), rules=None):
        args = ["snapshot", "--out", self.tmp / "spans.json"]
        if source is not None:
            args += ["--source", self.put("source.txt", source)]
        if context is not None:
            args += ["--context", self.put("context.txt", context)]
        code, _ = self.run_cli(*args)
        self.assertEqual(code, 0)
        d = self.put("candidate.md", draft)
        out = self.tmp / "final.md"
        if out.exists():
            out.unlink()
        args = ["finalize", "--channel", channel, "--spans", self.tmp / "spans.json",
                "--draft", d, "--out", out, "--round", rnd]
        if template:
            args += ["--template", self.put("tpl.md", template)]
        if rules:
            args += ["--rules", self.put("rules.json", json.dumps(rules))]
        for o in omit:
            args += ["--omit", o]
        for a in allow:
            args += ["--allow", a]
        code, rep = self.run_cli(*args)
        return code, rep, (out.read_bytes() if out.exists() else None)


class Gate1NoPublishingSideEffects(CLI):
    def test_runner_starts_no_process(self):
        src = RUNNER.read_text()
        for bad in ("os.system", "os.popen", "socket", "urllib", "http.client", "os.exec", "Popen"):
            self.assertNotIn(bad, src)
        self.assertNotIn("subprocess", src)

    def test_every_command_runs_with_git_gh_shimmed(self):
        # cleanup asserts the shim log stayed empty
        self.run_cli("route", "--channel", "pr")
        self.run_cli("voice", "--channel", "pr")
        self.fin("see `git push` docs", "run `git push` later\n", channel="pr")

    def test_skill_text_only_mentions_publishing_commands_as_prohibitions(self):
        cmds = re.compile(r"git push|git commit|git rebase|gh pr create|gh pr edit|--force")
        for f in [REPO / "SKILL.md", *(REPO / "references").glob("*.md")]:
            for line in f.read_text().splitlines():
                if cmds.search(line):
                    self.assertRegex(line.lower(), r"never|not |no |removed|hand the text back",
                                     f"{f.name}: {line}")


class Gate2Routing(CLI):
    CASES = [
        ({"--channel": "slack"}, 0, "slack", "ghostwriter"),
        ({"--channel": "pr"}, 0, "pr", "pr-creator"),
        ({"--request": "draft a slack reply to Priya about the outage"}, 0, "slack", "ghostwriter"),
        ({"--request": "turn this ramble into a DM"}, 0, "slack", "ghostwriter"),
        ({"--request": "write the PR description for this branch"}, 0, "pr", "pr-creator"),
        ({"--request": "need a pull request title and body"}, 0, "pr", "pr-creator"),
        ({"--request": "reply to this review comment on my PR"}, 0, "pr-comment", "ghostwriter"),
        ({"--request": "write an email to the vendor"}, 0, "email", "ghostwriter"),
        ({"--request": "answer this email from Priya"}, 0, "email", "ghostwriter"),
        ({"--request": "write a commit message"}, 0, "commit", "repo-conventions"),
        ({"--channel": "email"}, 0, "email", "ghostwriter"),
        ({"--channel": "pr-comment"}, 0, "pr-comment", "ghostwriter"),
        ({"--channel": "commit"}, 0, "commit", "repo-conventions"),
        ({"--request": "draft release notes for 2.3"}, 0, "release-notes", "sepia"),
        ({"--request": "write the postmortem"}, 0, "postmortem", "sepia"),
        ({"--request": "file a jira ticket for this"}, 0, "ticket", "sepia"),
        ({"--request": "write a blog post"}, 0, "article", "sepia"),
        ({"--request": "update the README for the new flag"}, 0, "docs", "sepia"),
    ]

    def test_table(self):
        for args, want_code, channel, ruleset in self.CASES:
            with self.subTest(args=args):
                flag, val = next(iter(args.items()))
                code, out = self.run_cli("route", flag, val)
                self.assertEqual(code, want_code, out)
                self.assertEqual(out["channel"], channel)
                self.assertEqual(out["ruleset"], ruleset)
                self.assertEqual(out["supported"], want_code == 0)
                if want_code == 0:
                    self.assertTrue(Path(out["card"]).is_file())

    def test_ambiguous_and_unknown(self):
        code, out = self.run_cli("route", "--request", "write the PR description and post it in slack")
        self.assertEqual((code, sorted(out["matches"])), (64, ["pr", "slack"]))
        code, _ = self.run_cli("route", "--request", "make it better")
        self.assertEqual(code, 64)
        code, _ = self.run_cli("route", "--channel", "fax")
        self.assertEqual(code, 64)

    def test_editorial_rules_are_channel_owned(self):
        skill = (REPO / "SKILL.md").read_text()
        pr_card = (REPO / "references" / "pr.md").read_text()
        self.assertNotIn("tells.md", pr_card)
        self.assertNotIn("tells.md", (REPO / "references" / "commit.md").read_text())
        for card in ("professional", "release-notes", "postmortem", "ticket", "article", "docs"):
            self.assertNotIn("tells.md", (REPO / "references" / f"{card}.md").read_text())
        for card in ("slack", "email", "pr-comment"):
            self.assertRegex(skill, rf"references/{card}\.md`, then `references/tells\.md`")
        self.assertRegex(skill, r"tells\.md` applies to the three Ghostwriter channels only")
        runner = RUNNER.read_text()
        for tell in ("delve", "leverage", "moreover", "happy to help"):
            self.assertNotIn(tell, runner)


class Gate3ProtectedSpans(CLI):
    SLACK_SRC = FIX.joinpath("slack_source.txt").read_bytes()
    CODE = CODE

    def slack_draft(self, **swap):
        return slack_draft(**swap)

    def test_changed_spans_restored_byte_exact(self):
        draft = self.slack_draft(url="https://ci.example.com/runs/88123?tab=Logs",
                                 quote="hold until the canary is green",
                                 block=self.CODE.decode().replace("\r\n", "\n"))
        code, rep, out = self.fin(self.SLACK_SRC, draft)
        self.assertEqual(code, 0, rep)
        self.assertIn(b"https://ci.example.com/runs/88123?tab=logs", out)
        self.assertIn(b'"Hold until the canary is green"', out)
        self.assertIn(self.CODE, out)                           # CRLF restored inside LF draft
        self.assertEqual(len(rep["restored"]), 3, rep)
        self.assertTrue(rep["recheck_meaning"])

    def test_each_missing_auto_span_rejected(self):
        for key, kind in [("url", "url"), ("quote", "quote"), ("ticket", "identifier"),
                          ("code", "inline-code"), ("pr", "identifier")]:
            with self.subTest(kind=key):
                code, rep, out = self.fin(self.SLACK_SRC, self.slack_draft(**{key: "[gone]"}))
                self.assertEqual((code, out), (2, None), rep)
                self.assertTrue(any("missing protected span" in r for r in rep["rejected"]), rep)

    def test_missing_code_block_rejected(self):
        draft = self.slack_draft().split("rollback:")[0] + "owner ACME-311, fix in #77\n"
        code, rep, out = self.fin(self.SLACK_SRC, draft)
        self.assertEqual((code, out), (2, None))
        self.assertIn("(code)", " ".join(rep["rejected"]))

    def test_deliberate_omit_is_explicit(self):
        draft = self.slack_draft(url="[gone]")
        code, rep, _ = self.fin(self.SLACK_SRC, draft,
                                omit=["https://ci.example.com/runs/88123?tab=logs"])
        self.assertEqual(code, 0, rep)
        self.assertEqual(rep["omitted"], ["https://ci.example.com/runs/88123?tab=logs"])
        code, rep, _ = self.fin(self.SLACK_SRC, draft, omit=["https://typo.example"])
        self.assertEqual(code, 64)

    def test_duplicated_quote_and_code_rejected_url_repeat_allowed(self):
        q = "Hold until the canary is green"
        code, rep, _ = self.fin(self.SLACK_SRC, self.slack_draft() + f'again: "{q}"\n')
        self.assertEqual(code, 2)
        self.assertIn("duplicated protected span (quote)", rep["rejected"][0])
        code, rep, _ = self.fin(self.SLACK_SRC, self.slack_draft() + "again https://ci.example.com/runs/88123?tab=logs\n")
        self.assertEqual(code, 0, rep)

    def test_nested_protected_spans_preserve_restore_and_reject(self):
        source = 'check `refreshSession()` in `src/auth.ts` and "Session expired. Sign in again."'
        for channel in ("slack", "pr"):
            for draft in (source, source.replace("refreshSession", "refreshsession")):
                with self.subTest(channel=channel, draft=draft):
                    code, rep, out = self.fin(source, draft, channel=channel)
                    self.assertEqual((code, out), (0, source.encode()), rep)
                    spans = json.loads((self.tmp / "spans.json").read_text())["spans"]
                    self.assertEqual(next(s["count"] for s in spans if s["text"] == "src/auth.ts"), 1)
        for draft in (source.replace("refreshSession()", "missing()"),
                      source + ' "Session expired. Sign in again."'):
            code, rep, out = self.fin(source, draft)
            self.assertEqual((code, out), (2, None), rep)
        source = '[[keep]]call refreshSession() twice[[/keep]]'
        self.assertEqual(self.fin(source, "call refreshsession() twice")[0], 0)
        source = '```\nrefreshSession()\n```'
        self.assertEqual(self.fin(source, source)[0], 0)
        self.assertEqual(self.fin(source, source + "\n" + source)[0], 2)

    def test_quoted_code_literal_is_an_identifier_not_a_quote(self):
        # regression from the live run: metrics.incr("RetryBudgetExceeded") capped the name at one use
        src = 'metrics.incr("RetryBudgetExceeded")'
        draft = "raises `RetryBudgetExceeded` and counts RetryBudgetExceeded\n"
        code, rep, out = self.fin(src, draft)
        self.assertEqual((code, out), (0, draft.encode()), rep)

    def test_context_spans_protected_only_where_used(self):
        ctx = 'background: see https://wiki.example.com/Runbook and "Never Page Twice"'
        code, rep, out = self.fin(None, "short update, nothing else\n", context=ctx)
        self.assertEqual(code, 0, rep)
        code, rep, out = self.fin(None, "per https://wiki.example.com/runbook\n", context=ctx)
        self.assertEqual(code, 0, rep)
        self.assertEqual(out, b"per https://wiki.example.com/Runbook\n")

    def test_designated_span_exact_bytes_including_crlf_and_trailing_space(self):
        code, rep, out = self.fin(b"note [[keep]]flag:  ON \r\nstep 2[[/keep]] end",
                                  "set flag: on\nstep 2 then go\n")
        self.assertEqual(code, 0, rep)
        self.assertIn(b"flag:  ON \r\nstep 2", out)

    def test_missing_designated_span_rejected(self):
        code, rep, out = self.fin("[[keep]]ship behind flag new_checkout[[/keep]]", "ship it\n")
        self.assertEqual((code, out), (2, None))
        self.assertTrue(any("missing protected span (designated)" in r for r in rep["rejected"]), rep)

    def test_duplicated_designated_span_rejected(self):
        span = "rollback window closes 17:00 UTC"
        code, rep, out = self.fin(f"[[keep]]{span}[[/keep]]", f"{span}. repeat: {span}.\n")
        self.assertEqual((code, out), (2, None))
        self.assertIn("duplicated protected span", rep["rejected"][0])

    def test_designated_twice_in_source_needs_two(self):
        span = "do not page oncall"
        src = f"[[keep]]{span}[[/keep]] and again [[keep]]{span}[[/keep]]"
        self.assertEqual(self.fin(src, f"{span}\n")[0], 2)
        self.assertEqual(self.fin(src, f"{span}, {span}\n")[0], 0)

    def test_two_changed_candidates_for_one_span_rejected(self):
        code, rep, out = self.fin("[[keep]]Freeze Starts Friday[[/keep]]",
                                  "freeze starts friday. FREEZE STARTS FRIDAY.\n")
        self.assertEqual((code, out), (2, None))
        self.assertIn("ambiguous restoration", rep["rejected"][0])

    def test_one_region_matching_two_source_spans_rejected(self):
        code, rep, out = self.fin('quotes: "Merge After Review" and "merge after REVIEW"',
                                  "rule: merge after review\n")
        self.assertEqual((code, out), (2, None))
        self.assertTrue(any("ambiguous restoration" in r for r in rep["rejected"]), rep)

    def test_id_inside_branch_name_not_rewritten(self):
        # regression: ACME-412 must not "restore" into fix/acme-412-retry-budget
        src = "Ticket ACME-412 on branch fix/acme-412-retry-budget"
        for draft in ("fix/acme-412-retry-budget\n\n- capping retries (ACME-412)\n",
                      "fix/acme-412-retry-budget\n\n- see acme-412.\n"):
            with self.subTest(draft=draft):
                code, rep, out = self.fin(src, draft, channel="pr")
                self.assertEqual(code, 0, rep)
                self.assertIn(b"fix/acme-412-retry-budget\n", out)
        code, rep, out = self.fin(src, "fix/acme-412-retry-budget\n\n- see acme-412.\n", channel="pr")
        self.assertIn(b"- see ACME-412.\n", out)                  # standalone ID still restored

    def test_exact_region_beats_its_case_folded_twin(self):
        # regression (Build 3 eval): `us-ca` and `US-CA` are both spans; the draft uses each exactly
        draft = "the code `us-ca` no longer matches `US-CA`, so `us-ca` fails\n"
        code, rep, out = self.fin("codes `us-ca` and `US-CA`", draft, channel="postmortem")
        self.assertEqual((code, out), (0, draft.encode()), rep)
        code, rep, out = self.fin(None, draft, context="see `us-ca` and `US-CA`", channel="postmortem")
        self.assertEqual((code, out), (0, draft.encode()), rep)
        d2 = "run\n```\n   tessel token list\n```\nor `tessel token list`\n"
        code, rep, out = self.fin("```\ntessel token list\n```\nand `tessel token list`\n", d2, channel="docs")
        self.assertEqual(code, 0, rep)

    def test_short_span_inside_larger_protected_span_in_other_case(self):
        # regression (Build 3 eval): DEPTH / kestrel / outbound inside a longer protected command or heading
        src = "check `relayctl queue depth --queue outbound.dlq`, then `DEPTH` and `Kestrel`"
        draft = "run `relayctl queue depth --queue outbound.dlq`, then `DEPTH` and `Kestrel`\n"
        code, rep, out = self.fin(src, draft, channel="docs")
        self.assertEqual((code, out), (0, draft.encode()), rep)
        code, rep, out = self.fin("```\nkestrel --serve\n```\nand `kestrel`", "```\nkestrel --serve\n```\nand `kestrel`\n# Kestrel on Kubernetes\n", channel="docs",
                                  context="Kestrel on Kubernetes")
        self.assertEqual(code, 0, rep)

    def test_required_span_only_inside_container_in_other_case_still_rejected(self):
        code, rep, out = self.fin("keep `MAX_BATCH_SIZE` and `set max_batch_size=1`", "`set max_batch_size=1`\n", channel="docs")
        self.assertEqual((code, out), (2, None), rep)

    def test_indented_fenced_block_in_a_list_is_preserved_not_reindented(self):
        # regression (Build 3 eval): a fence nested in a list item; the draft copies it verbatim
        doc = ("1. List tokens:\n\n   ```sh\n   tessel token list\n   ```\n\n"
               "2. Rotate:\n\n   ```text\n   Rotated tok_1 -> tok_2\n   Old secret valid until 2026-09-26\n   ```\n")
        for nl in ("\n", "\r\n"):
            with self.subTest(nl=repr(nl)):
                d = doc.replace("\n", nl)
                code, rep, out = self.fin(d, d, channel="docs")
                self.assertEqual((code, out), (0, d.encode()), rep)
                self.assertTrue(rep["unchanged"] and not rep["restored"], rep)
        # a changed nested block is still restored, without doubling the indentation
        drifted = doc.replace("Rotated tok_1 -> tok_2", "rotated tok_1 -> tok_2")
        code, rep, out = self.fin(doc, drifted, channel="docs")
        self.assertEqual((code, out), (0, doc.encode()), rep)

    def test_missing_indented_block_still_rejected(self):
        doc = "1. List tokens:\n\n   ```sh\n   tessel token list\n   ```\n"
        code, rep, out = self.fin(doc, "1. List tokens with the CLI.\n", channel="docs")
        self.assertEqual((code, out), (2, None), rep)

    def test_code_block_renested_at_another_depth_is_exact(self):
        # regression (Build 3 eval): same block, different list nesting; relative indentation is what counts
        src = "1. Set:\n\n   ```yaml\n   image:\n     repository: r\n   ```\n"
        flat = "Set:\n\n```yaml\nimage:\n  repository: r\n```\n"
        code, rep, out = self.fin(src, flat, channel="docs")
        self.assertEqual((code, out), (0, flat.encode()), rep)
        self.assertTrue(rep["unchanged"] and not rep["restored"], rep)
        nested = "- Set:\n\n  ```yaml\n  image:\n    repository: r\n  ```\n"
        code, rep, out = self.fin(flat, nested, channel="docs")
        self.assertEqual((code, out), (0, nested.encode()), rep)

    def test_code_block_lost_relative_indent_restored_with_the_drafts_own_nesting(self):
        src = "```yaml\nimage:\n  repository: r\n```\n"
        code, rep, out = self.fin(src, "```yaml\nimage:\nrepository: r\n```\n", channel="docs")
        self.assertEqual((code, out), (0, src.encode()), rep)
        nested_bad = "- Set:\n\n  ```yaml\n  image:\n  repository: r\n  ```\n"
        nested_ok = "- Set:\n\n  ```yaml\n  image:\n    repository: r\n  ```\n"
        code, rep, out = self.fin(src, nested_bad, channel="docs")
        self.assertEqual((code, out), (0, nested_ok.encode()), rep)
        sh = "```sh\nkubectl a\nkubectl b\n```\n"
        code, rep, out = self.fin(sh, "1. Run:\n\n   ```sh\n   kubectl a\n   Kubectl b\n   ```\n", channel="docs")
        self.assertEqual((code, out), (0, b"1. Run:\n\n   ```sh\n   kubectl a\n   kubectl b\n   ```\n"), rep)

    def test_plain_word_spans_are_not_restored_inside_prose(self):
        # regression (Build 3 eval): `run` / `validate` / `DEPTH` in the context must not re-case ordinary words
        ctx = "then `run` it, `validate` the config, check `DEPTH` and `refreshSession`"
        draft = "Run it. Validate the config. The depth is fine.\n"
        code, rep, out = self.fin(None, draft, context=ctx, channel="docs")
        self.assertEqual((code, out), (0, draft.encode()), rep)
        self.assertFalse(rep["restored"], rep)
        code, rep, out = self.fin(None, "call `refreshsession` first\n", context=ctx, channel="docs")
        self.assertEqual((code, out), (0, b"call `refreshSession` first\n"), rep)   # identifier-like: still restored

    def test_exact_diff_block_with_column_zero_lines_is_left_alone(self):
        # regression (Build 3 eval): a diff fence whose first line is a context line (leading space)
        doc = "```diff\n location /api {\n-    proxy_read_timeout 60s;\n+    proxy_read_timeout 6s;\n }\n```\n"
        code, rep, out = self.fin(doc, "The change:\n\n" + doc, channel="postmortem")
        self.assertEqual((code, out), (0, ("The change:\n\n" + doc).encode()), rep)
        self.assertTrue(rep["unchanged"], rep)

    def test_short_context_span_not_forced(self):
        code, rep, out = self.fin(None, "the api is fine\n", context="use `API` flag")
        self.assertEqual((code, out), (0, b"the api is fine\n"), rep)

    def test_non_utf8_rejected(self):
        code, rep, out = self.fin("x", b"caf\xe9\n")
        self.assertEqual((code, out), (2, None))


class Gate4CleanDraftsUnchanged(CLI):
    RULES = json.loads(FIX.joinpath("rules.sample.json").read_text())

    def test_clean_slack_bytes_identical(self):
        draft = slack_draft(nl="\r\n") + "caf\u00e9 thread is unrelated - ignore"  # CRLF, no final newline, non-ASCII
        code, rep, out = self.fin(FIX.joinpath("slack_source.txt").read_bytes(), draft, rules=self.RULES)
        self.assertEqual(code, 0, rep)
        self.assertTrue(rep["unchanged"])
        self.assertFalse(rep["recheck_meaning"])
        self.assertEqual(out, draft.encode("utf-8"))

    def test_clean_pr_bytes_identical(self):
        draft = FIX.joinpath("pr_clean.md").read_bytes()
        code, rep, out = self.fin(FIX.joinpath("pr_source.txt").read_bytes(), draft, channel="pr",
                                  rules=self.RULES)
        self.assertEqual(code, 0, rep)
        self.assertEqual(out, draft)

    def test_no_hardcoded_punctuation_bans(self):
        draft = "deploy is done \u2014 mostly \U0001F389\n"
        code, rep, out = self.fin("x", draft)
        self.assertEqual((code, out), (0, draft.encode()), rep)

    def test_user_rules_block_and_write_nothing(self):
        code, rep, out = self.fin("x", "deploy is done \u2014 mostly\n", rules=self.RULES)
        self.assertEqual((code, out), (1, None))
        self.assertIn("em/en dash", rep["errors"][0])

    def test_user_rules_scoped_by_channel(self):
        code, rep, _ = self.fin("x", "Ship it\n\n- done \U0001F389\n", channel="pr", rules=self.RULES)
        self.assertEqual(code, 0, rep)                            # emoji rule is slack-only
        code, rep, _ = self.fin("x", "done \U0001F389\n", rules=self.RULES)
        self.assertEqual(code, 1)

    def test_rule_exempts_protected_quote(self):
        code, rep, _ = self.fin('"Ship it \u2014 carefully" said the ticket',
                                'ticket says "Ship it \u2014 carefully"\n', rules=self.RULES)
        self.assertEqual(code, 0, rep)

    def test_style_is_not_linted(self):
        draft = "## heads up\n**bold** we will leverage the cache\n"
        code, rep, out = self.fin("x", draft)
        self.assertEqual((code, out, rep["warnings"]), (0, draft.encode(), []))

    def test_test_plan_needs_template_or_explicit_allow(self):
        draft = "Add retry budget\n\n## Test plan\n- [ ] replay canary\n"
        self.assertEqual(self.fin("x", draft, channel="pr")[0], 1)
        code, rep, out = self.fin("x", draft, channel="pr", template="## Summary\n\n## Test plan\n- [ ] item\n")
        self.assertEqual((code, out), (0, draft.encode()), rep)
        code, rep, out = self.fin("x", draft, channel="pr", allow=["test-plan", "checkboxes"])
        self.assertEqual((code, out), (0, draft.encode()), rep)
        self.assertEqual(self.fin("x", draft, channel="pr", allow=["test-plan"])[0], 1)

    def test_round_limit(self):
        self.assertEqual(self.fin("x", "fine\n", rnd=3)[0], 3)
        self.assertEqual(self.fin("x", "fine\n", rnd=2)[0], 0)

    def test_out_must_differ_from_draft(self):
        spans = self.put("spans.json", '{"version":2,"spans":[]}')
        d = self.put("c.md", "hi\n")
        code, _ = self.run_cli("finalize", "--channel", "slack", "--spans", spans, "--draft", d, "--out", d)
        self.assertEqual(code, 64)
        self.assertEqual(d.read_bytes(), b"hi\n")

    def test_mechanical_repetition_spacing_backtick(self):
        code, rep, out = self.fin("x", "fine and clean\n")
        self.assertEqual((code, rep["errors"], rep["warnings"]), (0, [], []), rep)
        self.assertEqual(out, b"fine and clean\n")
        for draft, bucket, msg in (("The the deploy\n", "errors", "repeated word"),
                                   ("ship it  today\n", "warnings", "two spaces between words"),
                                   ("run `make lint before push\n", "errors", "stray backtick")):
            with self.subTest(draft=draft):
                code, rep, _ = self.fin("x", draft)
                self.assertEqual(len(rep[bucket]), 1, rep)
                self.assertIn(msg, rep[bucket][0])
                self.assertEqual(code, 1 if bucket == "errors" else 0)
        # code, inline code, tables and protected source text are not prose
        for src, draft in (("x", "```sh\necho the the  x `\n```\n"),
                           ("x", "run `a  b` and `the the`\n"),
                           ("x", "| a  | b |\n|---|---|\n"),
                           ("x", "run ``echo the  the`` now\n"),
                           ("x", "# Deploy\n\nDeploy the service.\n"),
                           ('Dana wrote "ship the the build"', 'Dana wrote "ship the the build"\n')):
            with self.subTest(draft=draft):
                code, rep, _ = self.fin(src, draft)
                self.assertEqual((code, rep["errors"], rep["warnings"]), (0, [], []), rep)


class Gate5NoAttribution(CLI):
    BODY = "Add retry budget to checkout-api\n\n- capping retries at 3\n- logging budget exhaustion\n"

    def assert_no_leak(self, out=None):
        self.assertIsNone(LEAK.search(self.last_output.decode("utf-8")), self.last_output)
        if out is not None:
            self.assertIsNone(LEAK.search(out.decode("utf-8")), out)

    def test_each_footer_stripped_and_not_echoed(self):
        for footer in ATTRIBUTION_FOOTERS:
            with self.subTest(footer=footer):
                code, rep, out = self.fin("x", self.BODY + footer, channel="pr")
                self.assertEqual(code, 0, rep)
                kept = "\nThanks.\n" if footer.startswith("\nThanks.") else ""   # user's own word stays
                self.assertEqual(out, (self.BODY + kept).encode(), rep)
                self.assertTrue(rep["stripped_attribution"])
                self.assertEqual(set(rep["stripped_attribution"][0]), {"line", "code"})
                self.assert_no_leak(out)

    def test_all_footers_at_once_crlf(self):
        body = self.BODY.replace("\n", "\r\n")
        draft = body + "".join(ATTRIBUTION_FOOTERS).replace("\n", "\r\n")
        code, rep, out = self.fin("x", draft, channel="pr")
        self.assertEqual((code, out), (0, (body + "\r\nThanks.\r\n").encode()), rep)
        self.assert_no_leak(out)

    def test_removed_trailer_does_not_merge_paragraphs(self):
        draft = "first para\n\nCo-authored-by: Claude <noreply@anthropic.com>\nsecond para\n"
        code, rep, out = self.fin("x", draft)
        self.assertEqual((code, out), (0, b"first para\n\nsecond para\n"), rep)

    def test_inline_credit_and_session_link_removed_rest_kept(self):
        code, rep, out = self.fin("x", "context is in https://claude.ai/code/session_9 if needed\n")
        self.assertEqual((code, out), (0, b"context is in if needed\n"), rep)
        code, rep, out = self.fin("x", "done, ship it. Thanks. Generated with SomeNewTool\n")
        self.assertEqual((code, out), (0, b"done, ship it. Thanks.\n"), rep)
        self.assert_no_leak(out)

    BYLINES = [
        ("Generated with lowercasetool\n", "\n"),
        ("AI-generated draft\n", "\n"),
        ("*Generated with Claude*\n", "\n"),
        ("ok. _drafted with foo_\n", "ok.\n"),
        ("ok. **Generated with bar.** next\n", "ok. next\n"),
        ("- *made with Baz*\n", "\n"),
        ("**Written by gpt-5**\n", "\n"),
        ("ship status below (AI-generated)\n", "ship status below\n"),
        ("AI-assisted summary.\n", "\n"),
        ("ok. Disclosure: AI-assisted.\n", "ok.\n"),
        ("ship it (generated with zed)\n", "ship it\n"),
        ("Note: this summary is AI-generated. rest stays.\n", "rest stays.\n"),
        ("This description was written with help from Claude. Next.\n", "Next.\n"),
        ("Drafted with the help of ChatGPT.\n", "\n"),
        ("done. Prepared with assistance from somebot\n", "done.\n"),
    ]

    def test_general_byline_and_disclosure_classes(self):
        for draft, want in self.BYLINES:
            with self.subTest(draft=draft):
                code, rep, out = self.fin("x", "keep this line\n" + draft)
                self.assertEqual(code, 0, rep)
                self.assertEqual(out.decode(), ("keep this line\n" + want).rstrip("\n") + "\n", rep)
                self.assert_no_leak(out)

    def test_human_credits_kept_ai_self_ref_stripped(self):
        for draft in ("Made by Dana.\n", "Written by Dana Ruiz.\n",
                      "This description was written by Dana Ruiz.\n",
                      "This summary was written.\n"):
            with self.subTest(draft=draft):
                code, rep, out = self.fin("x", draft)
                self.assertEqual((code, out), (0, draft.encode()), rep)
        for draft in ("This description was written by Claude. Next.\n",
                      "This PR was generated using lowercasetool. Next.\n",
                      "This summary is AI-written. Next.\n"):
            with self.subTest(draft=draft):
                code, rep, out = self.fin("x", draft)
                self.assertEqual((code, out), (0, b"Next.\n"), rep)
                self.assert_no_leak(out)

    def test_ordinary_prose_about_generation_kept(self):
        for draft in ("the client is generated by protoc from api.proto\n",
                      "Generated by protoc from api.proto, so don't edit it.\n",
                      "the client, generated by protoc, is checked in\n",
                      "adds an AI-generated alt text option for images\n",
                      "AI-generated images improve accessibility.\n",
                      "Machine-written tests pass.\n",
                      "This PR adds files generated with protoc.\n",
                      "Generated by `protoc`.\n",
                      "we built this with sqlc\n",
                      "Built with love by the payments team, for the payments team.\n",
                      "Co-authored-by: Dana Ruiz <dana@example.com>\n"):
            with self.subTest(draft=draft):
                code, rep, out = self.fin("x", draft)
                self.assertEqual((code, out), (0, draft.encode()), rep)

    def test_factual_credit_from_source_or_context_kept(self):
        for sentence in ("Generated with sqlc.", "Built with stainless steel.", "Created using recycled paper."):
            with self.subTest(sentence=sentence):
                code, rep, out = self.fin(sentence, sentence + "\n", channel="docs")
                self.assertEqual((code, out), (0, (sentence + "\n").encode()), rep)
        code, rep, out = self.fin("x", "Generated with sqlc.\n", channel="docs", context="sqlc generate\n")
        self.assertEqual((code, out), (0, b"Generated with sqlc.\n"), rep)

    def test_unsourced_or_ai_credit_still_stripped(self):
        code, rep, out = self.fin("ship notes", "ship notes\nGenerated with sqlc.\n", channel="docs")
        self.assertEqual((code, out), (0, b"ship notes\n"), rep)
        code, rep, out = self.fin("Generated with Claude.", "ok.\nGenerated with Claude.\n", channel="docs")
        self.assertEqual((code, out), (0, b"ok.\n"), rep)
        self.assert_no_leak(out)

    def test_self_ref_and_robot_bylines_stripped_even_when_tool_supplied(self):
        for line in ("This response was drafted with SomeNewTool.", "\U0001F916 Generated with SomeNewTool"):
            for src, ctx in ((line, None), ("notes", "SomeNewTool is installed\n")):
                with self.subTest(line=line, ctx=ctx):
                    code, rep, out = self.fin(src, "ok.\n" + line + "\n", channel="docs", context=ctx)
                    self.assertEqual((code, out), (0, b"ok.\n"), rep)
                    self.assert_no_leak(out)

    def test_wrapped_credit_with_supplied_name_kept_and_flagged(self):
        # fact or byline cannot be told apart from the text alone: keep it and make the drafter ask
        for line in ("**Built with stainless steel.**", "**Generated with sqlc.**", "(Created using recycled paper.)",
                     "*Generated with SomeNewTool*", "ship it (generated with SomeNewTool)"):
            with self.subTest(line=line):
                code, rep, out = self.fin(line + " SomeNewTool", line + "\n", channel="docs")
                self.assertEqual((code, out), (0, (line + "\n").encode()), rep)
                self.assertTrue(any("possible-byline" in w for w in rep["warnings"]), rep)

    def test_attribution_inside_designated_span_rejected_without_echo(self):
        src = "[[keep]]fix typo\n\nCo-Authored-By: Claude <noreply@anthropic.com>[[/keep]]"
        draft = "commit to cherry-pick:\nfix typo\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n"
        code, rep, out = self.fin(src, draft)
        self.assertEqual((code, out), (2, None))
        self.assertIn("attribution-in-protected-text", rep["rejected"][0])
        self.assert_no_leak()

    def test_missing_attribution_span_diagnostic_is_scrubbed(self):
        src = "[[keep]]fix typo\n\nCo-Authored-By: Claude <noreply@anthropic.com>[[/keep]]"
        code, rep, out = self.fin(src, "fix typo only\n")
        self.assertEqual((code, out), (2, None))
        self.assert_no_leak()

    def test_attribution_inside_code_block_rejected(self):
        src = "```\ngit log shows:\nGenerated with Claude Code\n```"
        draft = "the old commit says\n```\ngit log shows:\nGenerated with Claude Code\n```\n"
        code, rep, out = self.fin(src, draft)
        self.assertEqual((code, out), (2, None))
        self.assert_no_leak()

    def test_session_url_inside_protected_quote_rejected(self):
        src = 'Dana wrote "see https://claude.ai/code/session_42 for the trace"'
        code, rep, out = self.fin(src, src + "\n")
        self.assertEqual((code, out), (2, None))
        self.assert_no_leak()

    def test_voice_root_expands_tilde(self):
        env = {**os.environ, "GHOSTWRITER_HOME": "~/custom-gw-probe"}
        p = subprocess.run([sys.executable, str(RUNNER), "voice", "--channel", "slack"],
                           capture_output=True, env=env)
        self.assertEqual(json.loads(p.stdout)["root"], str(Path.home() / "custom-gw-probe"))

    def test_scoped_claude_settings_turn_attribution_off(self):
        cfg = json.loads((REPO / "config" / "claude-settings.json").read_text())
        self.assertEqual(cfg["attribution"], {"commit": "", "pr": ""})


class Gate6Build2Channels(CLI):
    """Email, PR comments and commit messages: routing cards, profiles, format, preservation."""
    COMMIT_SRC = ("Fix retry budget in refreshSession() for ACME-311, see #412 and "
                  "https://ci.example.com/runs/88123?tab=logs")
    COMMIT = ("Fix retry budget in `refreshSession()`\n\nCap retries at 3 so ACME-311 stops looping, see #412 "
              "and https://ci.example.com/runs/88123?tab=logs\n")
    EMAIL_SRC = 'Priya wrote "Renewal closes on 2026-10-15" and sent https://vendor.example.com/quote/77'
    EMAIL = ('Subject: Re: Vendor renewal\n\nPriya, you said "Renewal closes on 2026-10-15". I will confirm '
             'the seats before then. Quote: https://vendor.example.com/quote/77\n')
    COMMENT_SRC = "Reviewer: \"why not reuse retry_budget\"?\n```\nsuggestion_line = retry_budget\n```"
    COMMENT = ("Good catch, `retry_budget` is reused now. You asked \"why not reuse retry_budget\":\n"
               "```\nsuggestion_line = retry_budget\n```\n")
    CASES = [("email", EMAIL_SRC, EMAIL), ("pr-comment", COMMENT_SRC, COMMENT), ("commit", COMMIT_SRC, COMMIT)]
    RULES = json.loads(FIX.joinpath("rules.sample.json").read_text())

    def test_cards_exist_and_each_channel_reads_only_its_own(self):
        for channel in ("email", "pr-comment", "commit"):
            code, out = self.run_cli("route", "--channel", channel)
            self.assertEqual(code, 0, out)
            self.assertEqual(Path(out["card"]).name, f"{channel}.md")
            self.assertTrue(Path(out["card"]).is_file())
        skill = (REPO / "SKILL.md").read_text()
        for name in ("email.md", "pr-comment.md", "commit.md"):
            self.assertIn(f"references/{name}", skill)

    def test_ambiguous_across_new_channels(self):
        for req in ("write the PR description and a commit message", "email the vendor and post it in slack"):
            with self.subTest(req=req):
                code, out = self.run_cli("route", "--request", req)
                self.assertEqual(code, 64, out)
                self.assertGreaterEqual(len(out["matches"]), 2)

    def test_profile_resolves_per_channel_and_falls_back(self):
        gw = self.tmp / "gw"
        gw.mkdir()
        (gw / "email.md").write_text("email voice")
        (gw / "pr.md").write_text("pr voice")
        (gw / "persona.md").write_text("persona")
        for channel, has in (("email", True), ("pr-comment", False), ("commit", False)):
            with self.subTest(channel=channel):
                code, out = self.run_cli("voice", "--channel", channel)
                self.assertEqual(code, 0)
                if has:
                    self.assertEqual(out["profile"], str(gw / f"{channel}.md"))
                    self.assertIsNone(out["persona_fallback"])
                else:   # pr.md is the PR title/body profile; it does not stand in for another channel
                    self.assertIsNone(out["profile"])
                    self.assertEqual(out["persona_fallback"], str(gw / "persona.md"))
                    self.assertIn(channel, out["request"])
        elsewhere = self.put("elsewhere.md", "persona")
        code, out = self.run_cli("voice", "--channel", "commit", env={"GHOSTWRITER_PERSONA": str(elsewhere)})
        self.assertEqual(out["persona_fallback"], str(elsewhere))

    def test_private_profile_root_is_never_listed_as_evidence_for_drafting(self):
        (self.tmp / "gw" / "imports" / "commit-samples").mkdir(parents=True)
        code, out = self.run_cli("voice", "--channel", "commit")
        self.assertEqual([Path(p).name for p in out["candidate_corpora"]], ["commit-samples"])
        self.assertNotIn("commit-samples", (REPO / "references" / "commit.md").read_text())

    def test_clean_drafts_unchanged_byte_for_byte(self):
        for channel, src, draft in self.CASES:
            for nl in ("\n", "\r\n"):
                with self.subTest(channel=channel, nl=repr(nl)):
                    d = draft.replace("\n", nl)
                    code, rep, out = self.fin(src, d, channel=channel, rules=self.RULES)
                    self.assertEqual(code, 0, rep)
                    self.assertTrue(rep["unchanged"])
                    self.assertFalse(rep["recheck_meaning"])
                    self.assertEqual(out, d.encode())

    def test_every_missing_protected_span_rejected_in_each_channel(self):
        for channel, src, draft in self.CASES:
            self.run_cli("snapshot", "--source", self.put("s.txt", src), "--out", self.tmp / "sp.json")
            spans = json.loads((self.tmp / "sp.json").read_text())["spans"]
            self.assertTrue(spans)
            for span in (sp["text"] for sp in spans):
                with self.subTest(channel=channel, span=span):
                    code, rep, out = self.fin(src, draft.replace(span, "X"), channel=channel)
                    self.assertEqual((code, out), (2, None), rep)

    def test_changed_case_identifier_restored_and_ambiguous_rejected(self):
        code, rep, out = self.fin(self.COMMIT_SRC, self.COMMIT.replace("ACME-311", "acme-311"), channel="commit")
        self.assertEqual(code, 0, rep)
        self.assertIn(b"ACME-311", out)
        self.assertTrue(rep["recheck_meaning"])
        code, rep, out = self.fin('Dana said "Hold The Line" and "hold the LINE"', "Subject: Re: freeze\n\nhold the line\n",
                                  channel="email")
        self.assertEqual((code, out), (2, None))
        self.assertTrue(any("ambiguous restoration" in r for r in rep["rejected"]), rep)

    def test_email_shape(self):
        ok = "Subject: Vendor renewal\n\nseats confirmed\n"
        self.assertEqual(self.fin("x", ok, channel="email")[0], 0)
        self.assertEqual(self.fin("x", ok, channel="email")[2], ok.encode())
        for bad in ("seats confirmed\n", "Subject:\n\nbody\n", "Subject: Vendor renewal\nseats confirmed\n"):
            with self.subTest(bad=bad):
                code, rep, out = self.fin("x", bad, channel="email")
                self.assertEqual((code, out), (1, None), rep)
        self.assertEqual(self.fin("x", "Subject: Just a subject\n", channel="email")[0], 0)

    def test_commit_shape_and_repo_stated_subject_limit(self):
        self.assertEqual(self.fin("x", "Fix retry budget\n", channel="commit")[0], 0)
        self.assertEqual(self.fin("x", "Fix retry budget\nbody right below\n", channel="commit")[0], 1)
        long_subject = "Fix " + "x" * 80 + "\n\nbody\n"
        self.assertEqual(self.fin("x", long_subject, channel="commit")[0], 0)   # no limit invented
        d = self.put("c.md", long_subject)
        self.run_cli("snapshot", "--source", self.put("s.txt", "x"), "--out", self.tmp / "spans.json")
        args = ["finalize", "--channel", "commit", "--spans", self.tmp / "spans.json", "--draft", d,
                "--out", self.tmp / "o.md"]
        code, rep = self.run_cli(*args, "--subject-max", "72")
        self.assertEqual(code, 1, rep)
        self.assertIn("repo limit 72", rep["errors"][0])
        self.assertFalse((self.tmp / "o.md").exists())
        self.assertEqual(self.run_cli(*args, "--subject-max", "100")[0], 0)

    def test_commit_style_is_the_repos_not_ours(self):
        for subject in ("feat(auth): add flow (ACME-9)", "add flow.", "ACME-9 Add flow", "Add flow"):
            with self.subTest(subject=subject):
                self.assertEqual(self.fin("x", subject + "\n", channel="commit")[0], 0)

    def test_pr_comment_has_no_imposed_structure(self):
        for draft in ("nit: rename this\n", "## heading\n- [ ] box\n## Test plan\n"):
            with self.subTest(draft=draft):
                code, rep, out = self.fin("x", draft, channel="pr-comment")
                self.assertEqual((code, out), (0, draft.encode()), rep)

    def test_user_rules_apply_per_channel_scope(self):
        rules = {"forbid": [{"pattern": "\u2014", "message": "em dash", "channels": ["email", "commit"]}]}
        for channel, draft, code_ in (("email", "Subject: A\n\nfine \u2014 ok\n", 1),
                                      ("commit", "Fix it \u2014 now\n", 1),
                                      ("pr-comment", "fine \u2014 ok\n", 0)):
            with self.subTest(channel=channel):
                self.assertEqual(self.fin("x", draft, channel=channel, rules=rules)[0], code_)

    def test_attribution_stripped_in_each_channel_and_human_trailers_kept(self):
        bodies = {"email": "Subject: Vendor renewal\n\nseats confirmed\n",
                  "pr-comment": "fixed in a1b2c3d, retries capped\n",
                  "commit": "Cap retries at 3\n\nStops the loop in checkout.\n"}
        for channel, body in bodies.items():
            for footer in ATTRIBUTION_FOOTERS:
                with self.subTest(channel=channel, footer=footer):
                    code, rep, out = self.fin("x", body + footer, channel=channel)
                    self.assertEqual(code, 0, rep)
                    kept = "\nThanks.\n" if footer.startswith("\nThanks.") else ""
                    self.assertEqual(out, (body + kept).encode(), rep)
                    self.assertIsNone(LEAK.search(self.last_output.decode()), self.last_output)
        human = "Cap retries at 3\n\nCo-authored-by: Dana <dana@example.com>\nFixes: #12\n"
        code, rep, out = self.fin("x", human, channel="commit")
        self.assertEqual((code, out), (0, human.encode()), rep)

    def test_attribution_inside_protected_text_rejected_in_each_channel(self):
        src = 'Dana wrote "see https://claude.ai/code/session_42 for the trace"'
        for channel in ("email", "pr-comment", "commit"):
            with self.subTest(channel=channel):
                draft = ("Subject: Re: trace\n\n" if channel == "email" else "") + src + "\n"
                code, rep, out = self.fin(src, draft, channel=channel)
                self.assertEqual((code, out), (2, None))
                self.assertIsNone(LEAK.search(self.last_output.decode()), self.last_output)

    def test_revision_limit_and_out_separate_in_each_channel(self):
        for channel, _, draft in self.CASES:
            with self.subTest(channel=channel):
                self.assertEqual(self.fin("x", draft, channel=channel, rnd=3)[0], 3)
                self.assertEqual(self.fin("x", draft, channel=channel, rnd=2)[0], 0)

    def test_no_publishing_side_effects_across_new_channels(self):
        # tearDown asserts the git/gh/curl/open/pbcopy shim log stayed empty
        for channel, src, draft in self.CASES:
            self.run_cli("route", "--channel", channel)
            self.run_cli("voice", "--channel", channel)
            self.assertEqual(self.fin(src, draft, channel=channel)[0], 0)


class Gate7ProfessionalDocuments(CLI):
    """Release notes, postmortems, tickets, articles and docs: cards, shape, long-form preservation."""
    CHANNELS = ("release-notes", "postmortem", "ticket", "article", "docs")
    URL = "https://status.example.com/incidents/2291"
    SRC = ("Postmortem inputs. Alert ACME-311 fired at [[keep]]14:07 UTC[[/keep]]. Dana wrote "
           '"Roll back the config, do not restart the pool" and linked ' + URL + ". The fix is in #412 "
           "and touches `db/pool.py`. Run:\n```sh\nkubectl rollout undo deploy/checkout-api\n```\n")
    DOC = (
        "# Checkout outage, 2026-09-14\n\n"
        "## Impact\n\n"
        "Checkout returned 5xx for 47 minutes. 3,112 requests failed.\n\n"
        "## Timeline\n\n"
        "| Time (UTC) | Event |\n|---|---|\n"
        "| 14:07 UTC | Alert ACME-311 fired |\n"
        "| 14:31 | We chased the load balancer for 24 minutes and it was fine |\n\n"
        "## Cause\n\n"
        "The deploy pipeline promoted a config with `db/pool.py` reading `POOL_MIN=0` before validation ran. "
        'Dana wrote "Roll back the config, do not restart the pool" and we did, see ' + URL + ".\n\n"
        "```sh\nkubectl rollout undo deploy/checkout-api\n```\n\n"
        "## Actions\n\n"
        "- [ ] Validate config before promotion (owner: infra, due 2026-10-01), fix in #412\n"
        "- [ ] Alert on queue depth over 10k (owner: platform)\n"
    )
    RULES = json.loads(FIX.joinpath("rules.sample.json").read_text())

    def test_cards_exist_and_professional_card_is_read_first(self):
        skill = (REPO / "SKILL.md").read_text()
        self.assertIn("references/professional.md", skill)
        for ch in self.CHANNELS:
            code, out = self.run_cli("route", "--channel", ch)
            self.assertEqual((code, out["ruleset"], Path(out["card"]).name), (0, "sepia", f"{ch}.md"), out)
            self.assertTrue(Path(out["card"]).is_file())
            card = Path(out["card"]).read_text()
            self.assertIn("professional.md", card)
            self.assertIn(f"`{ch}.md`", skill)
            self.assertIn("Sepia", (REPO / "PROVENANCE.md").read_text())

    def test_professional_ambiguity_rejected(self):
        code, out = self.run_cli("route", "--request", "write release notes and a postmortem")
        self.assertEqual((code, sorted(out["matches"])), (64, ["postmortem", "release-notes"]))

    def test_profile_resolves_per_professional_channel(self):
        gw = self.tmp / "gw"
        gw.mkdir()
        (gw / "article.md").write_text("article voice")
        (gw / "persona.md").write_text("persona")
        for ch in self.CHANNELS:
            with self.subTest(channel=ch):
                code, out = self.run_cli("voice", "--channel", ch)
                self.assertEqual(code, 0)
                if ch == "article":
                    self.assertEqual(out["profile"], str(gw / "article.md"))
                else:
                    self.assertIsNone(out["profile"])
                    self.assertEqual(out["persona_fallback"], str(gw / "persona.md"))

    def test_clean_long_documents_unchanged_byte_for_byte(self):
        for ch in ("postmortem", "docs", "article", "release-notes"):
            for nl in ("\n", "\r\n"):
                with self.subTest(channel=ch, nl=repr(nl)):
                    d = self.DOC.replace("\n", nl)
                    code, rep, out = self.fin(self.SRC, d, channel=ch, rules=self.RULES)
                    self.assertEqual(code, 0, rep)
                    self.assertEqual(out, d.encode())
                    self.assertTrue(rep["unchanged"])
                    self.assertFalse(rep["recheck_meaning"])

    def test_mechanical_does_not_flag_headings_tables_lists_code(self):
        for ch in ("postmortem", "docs", "release-notes"):
            with self.subTest(channel=ch):
                code, rep, out = self.fin(self.SRC, self.DOC, channel=ch)
                self.assertEqual((code, rep["errors"], rep["warnings"]), (0, [], []), rep)
                self.assertEqual(out, self.DOC.encode())

    def test_every_missing_protected_span_rejected_in_each_channel(self):
        self.run_cli("snapshot", "--source", self.put("s.txt", self.SRC), "--out", self.tmp / "sp.json")
        spans = [sp for sp in json.loads((self.tmp / "sp.json").read_text())["spans"] if sp["required"]]
        self.assertGreaterEqual(len(spans), 6)
        for ch in self.CHANNELS:
            for sp in spans:
                with self.subTest(channel=ch, span=sp["text"]):
                    draft = ("Retry queue drops jobs\n\n" if ch == "ticket" else "") + self.DOC.replace(sp["text"], "X")
                    code, rep, out = self.fin(self.SRC, draft, channel=ch)
                    self.assertEqual((code, out), (2, None), rep)

    def test_designated_timestamp_needs_exact_bytes_and_count(self):
        code, rep, out = self.fin(self.SRC, self.DOC.replace("14:07 UTC", "14:07"), channel="postmortem")
        self.assertEqual((code, out), (2, None), rep)
        code, rep, out = self.fin(self.SRC, self.DOC + "14:07 UTC again\n", channel="postmortem")
        self.assertEqual((code, out), (2, None), rep)

    def test_changed_case_id_restored_and_ambiguous_rejected(self):
        code, rep, out = self.fin(self.SRC, self.DOC.replace("ACME-311", "acme-311"), channel="postmortem")
        self.assertEqual(code, 0, rep)
        self.assertIn(b"ACME-311", out)
        self.assertTrue(rep["recheck_meaning"])
        code, rep, out = self.fin('Cite "Hold The Line" and "hold the LINE"', "we hold the line\n", channel="article")
        self.assertEqual((code, out), (2, None))
        self.assertTrue(any("ambiguous restoration" in r for r in rep["rejected"]), rep)

    def test_ticket_shape(self):
        ok = "Retry queue drops jobs on redeploy\n\nRepro: redeploy while a job is queued.\n"
        self.assertEqual(self.fin("x", ok, channel="ticket")[2], ok.encode())
        for bad in ("Retry queue drops jobs\nbody right under\n", "\n\nbody only\n"):
            with self.subTest(bad=bad):
                self.assertEqual(self.fin("x", bad, channel="ticket")[0], 1)
        self.assertEqual(self.fin("x", "Just a title\n", channel="ticket")[0], 0)

    def test_documents_have_no_imposed_structure_or_pr_only_checks(self):
        for ch in ("release-notes", "postmortem", "article", "docs"):
            for draft in ("no heading at all, just prose\n", "## Test plan\n- [ ] item\n"):
                with self.subTest(channel=ch, draft=draft):
                    code, rep, out = self.fin("x", draft, channel=ch)
                    self.assertEqual((code, out), (0, draft.encode()), rep)

    def test_style_is_not_linted_in_professional_channels(self):
        draft = "We are excited to leverage a robust, seamless deep dive.\n"
        for ch in self.CHANNELS:
            with self.subTest(channel=ch):
                code, rep, out = self.fin("x", ("Title\n\n" if ch == "ticket" else "") + draft, channel=ch)
                self.assertEqual(code, 0, rep)

    def test_attribution_stripped_and_human_credit_kept_in_each_channel(self):
        base = {"release-notes": "## 2.3.0\n\n- fix retry race (#412)\n",
                "postmortem": self.DOC, "article": "We hit a retry race.\n",
                "docs": "# Install\n\nRun `make install`.\n", "ticket": "Retry queue drops jobs\n\nRepro below.\n"}
        src = {"postmortem": self.SRC}
        for ch, body in base.items():
            for footer in ATTRIBUTION_FOOTERS:
                with self.subTest(channel=ch, footer=footer):
                    code, rep, out = self.fin(src.get(ch, "x"), body + footer, channel=ch)
                    self.assertEqual(code, 0, rep)
                    kept = "\nThanks.\n" if footer.startswith("\nThanks.") else ""
                    self.assertEqual(out, (body + kept).encode(), rep)
                    self.assertIsNone(LEAK.search(self.last_output.decode()), self.last_output)
        human = "## 2.3.0\n\n- fix retry race\n\nThanks @dana for #398\nCo-authored-by: Dana <dana@example.com>\n"
        code, rep, out = self.fin("x", human, channel="release-notes")
        self.assertEqual((code, out), (0, human.encode()), rep)

    def test_attribution_inside_protected_citation_rejected(self):
        src = 'The vendor wrote "see https://claude.ai/code/session_42 for the trace"'
        for ch in self.CHANNELS:
            with self.subTest(channel=ch):
                draft = ("Title\n\n" if ch == "ticket" else "") + src + "\n"
                code, rep, out = self.fin(src, draft, channel=ch)
                self.assertEqual((code, out), (2, None))
                self.assertIsNone(LEAK.search(self.last_output.decode()), self.last_output)

    def test_user_rules_scope_and_revision_limit(self):
        rules = {"forbid": [{"pattern": "\u2014", "message": "em dash", "channels": ["postmortem"]}]}
        self.assertEqual(self.fin("x", "fine \u2014 ok\n", channel="postmortem", rules=rules)[0], 1)
        self.assertEqual(self.fin("x", "fine \u2014 ok\n", channel="article", rules=rules)[0], 0)
        for ch in self.CHANNELS:
            with self.subTest(channel=ch):
                d = ("Title\n\n" if ch == "ticket" else "") + "fine\n"
                self.assertEqual(self.fin("x", d, channel=ch, rnd=3)[0], 3)
                self.assertEqual(self.fin("x", d, channel=ch, rnd=2)[0], 0)

    def test_no_publishing_side_effects_across_professional_channels(self):
        for ch in self.CHANNELS:   # tearDown asserts the git/gh/curl/open/pbcopy shim log stayed empty
            self.run_cli("route", "--channel", ch)
            self.run_cli("voice", "--channel", ch)
            d = ("Title\n\n" if ch == "ticket" else "") + "body\n"
            self.assertEqual(self.fin("x", d, channel=ch)[0], 0)


if __name__ == "__main__":
    unittest.main()
