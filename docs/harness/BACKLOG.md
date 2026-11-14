# BACKLOG — the harness's technical wants

Every technical want of the lead's backlog that may be public, with its status and where it was
found: a LEDGER or FILE pointer where a public record holds it, an ORIGIN pointer where this file is
its first filing. A want's text is its filer's words, not a quotation; its pointer names the record.
Items awaiting the owner's approval, and items about local work that has no public remote, are kept
back. The format is in the docstring of tools/context.py; `python tools/context.py check` resolves
every pointer.

## topo-floor-guaranteed-only-for-acyclic-rows
- status: done
- scope: Concordance-V3
- source: FILE Concordance-V3 MEASURED.md 842938686b1a1bb9ea7accccaf9b72c03611153a "For the 53 acyclic rows the floor is guaranteed by construction"
> The 2-pass floor is guaranteed only for acyclic rows: Kahn's order leaves a cycle's steps in listed
> order, and their floor depends on that order. MEASURED.md must say the floor is guaranteed for the
> acyclic rows and only measured for the cyclic ones, and never claim it in general.

## topo-calls-counted-per-step-and-spec
- status: done
- scope: Concordance-V3
- source: FILE Concordance-V3 MEASURED.md 842938686b1a1bb9ea7accccaf9b72c03611153a "`derivation.verify_step` by (domain, spec hash)"
> "One step called twice" cannot use a limit of 1 per (domain, spec hash): the three
> RECEIPT_REVERSE_CHAIN steps share one spec, so a correct run makes 3 calls. The per-key limit is
> the number of steps in the trail that carry that spec hash and whose verifier ran, hashing the spec
> the closure built and matching the domain lowercased, as verify_step does.

## topo-settled-only-planted-defect
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-topological-order 4
> A planted defect that changes only the settled field: [a false, c uses b, b uses a], where c gets an
> origin only when it is visited before b. The response is unchanged, because broken_at still names a.

## topo-replica-restores-the-order
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-topological-order 4
> order_replica._run with no order leaves whatever function is installed in place, and restores it
> afterwards.

## r4-default-table-pinned-to-the-verifier
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 11
> R4's default table is a second copy of the verifier's defaults (variable defaults to "x" in five
> modes), and R4 cannot import concordance.verifiers, so a test checks the table against the
> spec.get("variable", "x") lines of mathematics.py, read as text.

## r4-variables-as-a-dict
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 11
> Inequality claims carry variables as a dict: all 14 benchmark inequality claims have
> "variables": {}. R4 must understand that form or decline the mode.

## frame-seq-test-moves-with-its-fix
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 7
> The frame_seq test pins today's defective BROKEN reading, so it goes red when the fix lands; the
> fixing run updates it, as with a KNOWN entry.

## frame-seq-not-measured-by-the-audit
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 34
> The goal says frame_seq is "not measured here", while RECORDED adds a test that recomputes it: the
> goal means the audit does not measure it, and MEASURED.md must hold to that distinction.

## v3-ship-path
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 6
> V3's ship path (THE_PATH run 3): the hazards of deploy/install.sh, and the sha-checked launcher
> committed as a reviewed tool.

## false-goldens-read-system-error
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> False goldens: agriculture "7b_NOT" and oceanography "marine_NOT" read SYSTEM_ERROR. The fix may be
> a better golden (a valid but wrong value) rather than a verifier change.

## pressure-fighting-frame-seq-type
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 7
> pressure_fighting frame_seq 1 -> 1.0 reads BROKEN for a true claim (pressure_fighting.py:92): a
> type check reads a malformed input as a broken claim.

## integrations-pyproject-license
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 8
> integrations/pyproject.toml has the same deprecated license table, classifier and setuptools>=68,
> whose support ends 2027-02-18; it is fixed as a normal harness step.

## vocab-gate-skips-measured-md
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> vocab_gate does not scan MEASURED.md.

## pressure-fighting-test-order-dependence
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 22
> test_pressure_fighting::test_malformed_observation_is_rejected is order-dependent: it fails after
> test_claim_grammar.py, whose import-time CONCORDANCE_DATA_DIR setter (and about four like it) hides
> pfs_grammar.json. With bootstrap D's guard in place, a harness step can remove those setters.

## skipped-from-v2-lists-the-deleted-copies
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 22
> tests/SKIPPED_FROM_V2.txt should list the three deleted concordance-2 copies.

## write-guard-blind-spots
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 22
> D's write guard does not see os.link, os.symlink, os.chmod, os.utime or sqlite3.connect. No test
> uses them on data/ today.

## pending-seal-keeps-pq-null
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> A pending seal saved before a PQ key existed keeps pq null for good; publish_seals could add it.

## rotated-key-second-attestation
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> A settled seal under a rotated key still gets a second agentledger attestation (a gap in
> RECEIPT_SPEC §2c).

## get-of-a-pending-seal-publishes
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> On the box, a GET of a pending seal still triggers a publish (a product question).

## capabilities-reparses-the-benchmark
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> capabilities parses the 287 KB benchmark_last.json on every HOLDS (about 1 ms); an mtime cache would
> be cheap.

## in-suite-benchmark-load-flake
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 37
> The in-suite benchmark flakes under load: tests/test_benchmark.py::test_moat_is_green_zero_false_positives
> timed out on domain=statistics (a verify past 8 s is shed to ERROR, so a false negative only) in 4
> of the last 6 full laptop runs. check.py runs the plain benchmark as its own gate, which makes the
> in-suite run redundant: mark it slow, give it a test-only timeout, or drop it from the fast suite.
> Its own harness run.

## install-rewrites-a-tracked-file
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-02-gate-hygiene 32
> install.sh rewrote the tracked data/benchmark_last.json on the box and failed the gate-hygiene
> first ship. The ship-path run should make install.sh stop rewriting tracked files, or write
> --record, and then delete capabilities' second reader.

## health-names-the-served-commit
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-topological-order 20
> No public endpoint names the commit V3 serves: /health is {"ok": true}, /capabilities names the
> engine "concordance", and the Server header reads concordance/3. A commit field on /health, read
> from the installed tree and never hardcoded, would let a checker read the served sha. It changes
> the live engine, so it ships through install.sh.

## seals-order-is-not-newest-first
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 10
> /seals says "newest first", but its order does not follow sealed_at: the oldest seal, 75cf, is
> listed first.

## capabilities-ledger-entries-null
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 10
> /capabilities reports ledger.entries null, while /ledger/verify reports total 3.

## live-before-probe-pause
- status: done
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> An earlier live-before probe disabled its own 5 s pause and read /seals from one host only; the
> probe checker-28 corrected pauses for real and reads both hosts.

## org-health-commit-is-the-witness-app
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 10
> narrowhighway.org/health carries commit 819688b04a21, which is the witness app's commit, not V3's;
> it is never read as the commit V3 serves.

## restatement-record-states-coverage
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 34
> The restatement audit's record step states its coverage honestly: what R2, R3 and R4 reach in the
> benchmark and the tier, the MATH_VERIFY packets it declines and how many route to functions R2-R4
> map, and the numeric mode it leaves unmapped. The numbers, and the commit they were measured at,
> are in the record.

## restatement-r3-numeric-mode
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 34
> The restatement audit leaves the numeric mode unmapped: no benchmark case uses it, but tier steps
> do. R3 should reach it.

## restatement-coverage-errored-column
- status: open
- scope: Concordance-V3
- source: ORIGIN 2026-11-03 lead
> Add an "errored" column to the restatement audit's coverage table, so that it agrees with the
> by-restatement counts (checker-28's note on audit-planted). About six lines and a test; its own
> small step.

## restatement-math-verify-packets
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 11
> The restatement audit's R2-R4 map MATH_VERIFY packets, which they decline today.

## restatement-audit-exit-code-for-errors
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 28
> restatement_audit: an uncaught exception exited 1, the same code as a real exit-1 change; it needs
> a distinct code (step audit-planted gives it exit 3).

## restatement-timing-with-its-load
- status: done
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 34
> MEASURED.md quotes the restatement audit's times with the machine and its load, never a bare time.

## gcd-lcm-sign-depends-on-symbol-names
- status: open
- scope: Concordance-V3
- source: LEDGER Concordance-V3 2026-11-03-restatement-audit 21
> The mathematics verifier compares a sign-ambiguous polynomial gcd or lcm exactly, so its verdict
> depends on the symbols' names (sympy picks the sign by their alphabetical order): a potential false
> positive. Filed as its own run; until it lands, no V3 change to the gcd and lcm handling ships.

## context-and-rules-into-machinery
- status: open
- scope: concordance-2
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 10
> Add tools/context.py and docs/harness/RULES.md to MACHINERY by a reviewed bootstrap, because once
> briefs are built from them they tell checkers what to hold.

## spectral-rule-ranking
- status: open
- scope: concordance-2
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 10
> A spectral (eigenvector) ranking of the rules, measured once checkers' confirmations give a
> co-confirmation matrix. On an acyclic citation graph, power iteration reduces to plain counts.

## public-repo-rule-against-the-runbook
- status: open
- scope: concordance-2
- source: FILE concordance-2 docs/RUNBOOK.md 93b4446c20eff93e9281205672bdfffe4aedb8c8 "## 1. Topology — what runs where"
> docs/HARNESS.md's public-repo rule ('no box details') is broken by tracked content: the topology
> section of docs/RUNBOOK.md names the box's host, user, key file and paths.

## context-builds-its-own-secret-patterns
- status: done
- scope: concordance-2
- source: LEDGER concordance-2 2026-11-03-assemble-reapply 12
> tools/context.py builds its own secret-pattern list (the harness's SECRET_PATTERNS, then its
> configuration directory's secret_patterns.txt) and calls secret_kind with it, because setting
> HARNESS_SECRET_PATTERNS does not stop the harness reading its default file.

## live-check-fixture-is-fixed
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> The live check's fixed (run, step) is a fixture repository, or one generated at the pushed sha, so
> no later ledger event can change DUE or IN FLIGHT.

## check-names-its-config-dir
- status: done
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> tools/context.py check says which configuration directory it used, or none, because an accidental
> empty HARNESS_CONFIG_DIR silently turns off private-name scanning.

## scan-misses-system-paths
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> The records scan does not catch paths under /etc/, /srv/, /var/, /opt/ or /root/, UNC paths, or
> backslash paths without a drive letter, and the public RUNBOOK names box paths under /etc/ and
> /srv/.

## scan-flags-the-receipt-route
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> The scan's single-letter drive rule also flags V3's receipt route, whose first path segment is a
> single letter, so a public want that names the route is rephrased until the rule is narrowed.

## private-names-list-joined-forms
- status: done
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> The private-names file lists every joined form of a name explicitly, and never a phrase whose
> common word would become private; the docstring of tools/context.py says so.

## schedule-clock-reads-old-runs-at-the-records-commit
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-03 lead
> The schedule's clock uses done_problems from the records commit, so a later harness requirement
> could make old runs read incomplete and silently drop the run count; fixing that needs a reviewed
> bootstrap. A format change also refuses briefs for steps open across it, which is loud and safe.

## mint-handler-entries
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> The mint path takes data entries only: a handler entry of the catalog runs as Python in tools/tick.py,
> so tools/stick_mint.py refuses it, and minting handler entries through a gated path is a want. Named
> in the plan of run 2026-11-13-stick-ship, line 8.

## withdraw-cited-marks-and-notes
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> The keeping has no withdrawal for a cited mark or a note: a retract drops sealed marks by their seal
> alone, so the mint path's retract withdraws sealed marks only, and an entry's cited marks and notes are
> reviewed as tracked source before they mint. Named in the plan of run 2026-11-13-stick-ship, line 8.

## public-stick-and-tick-doors
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> The public POST /stick and POST /tick doors let anyone add a stick, or a cited mark or a note, to the
> live keeping. They are no ship path; whether they stay open is the owner's to decide. Named in the
> plan of run 2026-11-13-stick-ship, line 8.

## live-seals-older-than-the-seal-path
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> 63 of the catalog's 143 data entries with seals carry live marks whose seals are not the hashes
> today's seal path mints (60 carry none of them; 3 carry some: black_holes, gravity, linear_algebra),
> so listing one in tools/stick_mints.txt would add a second, newly sealed copy of each sealed mark
> beside the old. A decision for the owner before any such entry is listed. Named in the plan of run
> 2026-11-13-stick-ship, line 33.

## spine-card-named-whenever-a-mint-creates-an-object
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> tools/stick_mint.py's WOULD ADD names the receipt spine card only when data/receipt_cards.jsonl
> lacks it, while the cold seal path writes it again in each process that creates an object, so a
> mint that creates one adds a spine line WOULD ADD did not name; it should name it whenever the mint
> will create an object. Named in the plan of run 2026-11-13-ai-era-marks, line 8.

## remove-an-entry-from-the-box-catalog
- status: open
- scope: concordance-2
- source: ORIGIN 2026-11-13 lead
> No gated path removes an entry from the box's catalog (the box's data/sticks/<name>.json): an
> ordinary deploy only sends files. A gated path that removes one is a want, so that a revert of a
> seal shape can follow a retract. Named in the plan of run 2026-11-13-ai-era-marks, line 8.
