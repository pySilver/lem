Human-practice evidence: from a product request to a merged change

I opened each source below. Most numbers come from the PDF text, which I extracted and searched. A "vendor" label means that the publisher sells the tool or practice it studied.

1. WHERE REVIEW EFFORT PAYS

- At Google, the median change is 24 lines, and more than 35% of changes touch one file. The median reviewer count is 1, and fewer than 25% of changes have more than one reviewer. The median latency for the whole review is under 4 hours. The first feedback comes in under 1 hour for small changes and about 5 hours for very large ones. 70% of changes are committed less than 24 hours after they are sent for review. Sadowski et al., ICSE-SEIP 2018, https://sback.it/publications/icse2018seip.pdf
- The same Google paper says that review expectations center on education, norms, gatekeeping and accident prevention. Its words: "Defect finding is welcomed but not the only focus."
- At Microsoft, 44% of 873 programmers ranked "finding defects" as their first motivation. But only 14% of 570 sampled review comments (78) were about defects, and 29% (165) were about code improvements. Bacchelli and Bird, ICSE 2013, https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ICSE202013-codereview.pdf
- In two OSS projects, the changes that review caused split about 75:25 between evolvability and function. Beller et al., MSR 2014, http://sback.it/publications/msr2014.pdf
- AMD, Microsoft, Chrome and Android converged on a median of two active reviewers. More reviewers gave only a "minimal increase" in comments. Review made a developer aware of 66% to 150% more files (median case). Median approval times were 14.7 to 20.8 hours. Rigby and Bird, FSE 2013, https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/rigby2013convergent.pdf
- Cisco data (vendor study): 2,500 reviews, 3.2M LOC, 50 developers, 10 months.
  - Defect density fell above about 200 lines.
  - Above 450 LOC/hour, density was below average in 87% of cases.
  - 61% of reviews found no defects.
  - The advice is under 200 LOC, not more than 400, and under 60 minutes.
  - SmartBear/Cohen, 2006, https://static1.smartbear.co/support/media/resources/cc/book/code-review-cisco-case-study.pdf
- Google guidance says that 100 lines is "usually reasonable" and 1,000 is "usually too large". It sets one business day as the maximum time to respond to a review. Google eng-practices, https://google.github.io/eng-practices/review/developer/small-cls.html and https://google.github.io/eng-practices/review/reviewer/speed.html
- Teams with faster code reviews have "50% higher software delivery performance". DORA 2023 report, https://services.google.com/fh/files/misc/2023_final_report_sodr.pdf

2. DORA / ACCELERATE

- Quote: "formal change management processes that require the approval of an external body such as a change advisory board (CAB) or a senior manager for significant changes have a negative impact on software delivery performance." Respondents were 2.6 times more likely to be low performers when their organization had such a process. DORA 2019, https://services.google.com/fh/files/misc/state-of-devops-2019.pdf
- Quote, same report: "we found no evidence" that a more formal approval process was associated with lower change fail rates. It recommends a "shift left" to peer-review-based approval plus automation (CI, continuous testing, monitoring).
- On peer review, DORA 2019 lets segregation of duties come from team code review, "either prior to commit… (as part of pair programming) or prior to merge into master." https://dora.dev/capabilities/streamlining-change-approval/
- For high performers, "branch life and integration typically [last] hours"; for low performers they last days. The practices are fewer than three active branches and merges to trunk each day. The report says to "avoid keeping branches alive more than a day." DORA 2017, https://dora.dev/research/2017/2017-state-of-devops-report.pdf
- Small batches: features should take "no more than a few days", and a batch that takes longer than a week "is too big." https://dora.dev/capabilities/working-in-small-batches/
- In 2024, each 25% increase in AI adoption went with an estimated 1.5% decrease in throughput and 7.2% decrease in stability. DORA's hypothesis is that "changelists are growing in size." DORA 2024, https://dora.dev/research/2024/dora-report/2024-dora-accelerate-state-of-devops-report.pdf

3. RISK-TIERED REVIEW

- Ship/Show/Ask defines three modes: Ship (merge without review), Show (open a PR, then merge without a wait) and Ask (wait for feedback).
  - Safeguards: CI, a mainline that stays releasable, feature toggles, automated checks before a Show, short branches and team trust.
  - Approval is not a merge gate.
  - Regulated industries need review on every change.
  - Wilsenach, martinfowler.com, 2021, https://martinfowler.com/articles/ship-show-ask.html
- Apache measured both modes. Commit-then-review was for trusted core developers who were confident; review-then-commit was for complex work or outsiders.
  - The first post-commit response came in a median 1.7 hours.
  - Commit-then-review was 2.2 times faster.
  - Defects found showed no significant difference (p=0.80, 100-review samples).
  - The risk: a change that is not reviewed at once is rarely reviewed later ("commit-then-whatever").
  - Rigby, German, Storey, ICSE 2008, https://users.encs.concordia.ca/~pcr/paper/Rigby2008ICSE.pdf
- "Refinement code review" means review each time someone reads the code. Its preconditions are self-testing code, CI, refactoring skill and collective ownership. Security still gets targeted review. Fowler, 2021, https://martinfowler.com/bliki/RefinementCodeReview.html
- Google needs three approvals: LGTM, OWNERS and readability. Usually one person gives all three, and only one LGTM is needed by default. Machine-generated changes and rollbacks still get review, but global approvers review low-risk large-scale changes. Software Engineering at Google, ch. 9, 2020, https://abseil.io/resources/swe-book/html/ch09.html
- From March 24, 2021, Chromium made review and OWNERS approval mandatory and removed TBR, because "TBR was used to bypass OWNERS". The stated reason is "integrity of Chrome source code."
  - A bot (Rubber Stamper) approves "verifiably safe" changes: clean reverts, cherry-picks and translations.
  - It never gives OWNERS approval, so that nobody can do a "silent revert of security patches."
  - https://chromium.googlesource.com/chromium/src/+/main/docs/code_review_owners.md and https://chromium.googlesource.com/chromium/src/+/HEAD/docs/code_reviews.md
- Dependency auto-merge depends on required status checks. GitHub's example merges only semver-patch updates. Renovate does not auto-merge until checks pass. It recommends auto-merge "where you would select merge anyway" (devDependencies, lockfile maintenance, lint tools), and good test coverage for production dependencies. https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions and https://docs.renovatebot.com/key-concepts/automerge/

4. DISCUSSION BEFORE CODE

- Google design docs: "Writing design docs is overhead." The test is whether the solution is ambiguous. The author gives a 5-question test and says to write a doc at 3 or more "yes" answers. A doc that is "really an implementation manual" means you should write the code. Size: 10–20 pages for a large project, 1–3 pages for a mini doc. Ubl, 2020, https://www.industrialempathy.com/posts/design-docs-at-google/
- Rust needs an RFC only for "substantial" changes. Refactors, objective improvements and changes only Rust developers see need no RFC. Informal pre-RFC talk happens first. https://github.com/rust-lang/rfcs/blob/master/README.md
- Uber wrote RFCs "for every project that is beyond some super trivial complexity", with a few named approvers. The process scaled from tens of engineers to low thousands. Noise made Uber move to per-domain lists and templates. Orosz, 2018/2022, https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs/
- Three amigos means business, development and test perspectives on an increment, before, during and after the work. The named pitfall is that it becomes a regular ceremony. Agile Alliance (term from Dinwiddie, 2009), https://agilealliance.org/glossary/three-amigos/
- Shape Up keeps shaping (rough, solved, bounded) on a track separate from building. It fixes the "appetite" (time allowed), not an estimate, with six-week cycles. Singer/37signals, https://basecamp.com/shapeup/1.1-chapter-02

5. PAIR AND MOB PROGRAMMING

- The meta-analysis found a "small significant positive" effect on quality, a medium positive effect on duration and a medium negative effect on effort. It also found high between-study variance and signs of publication bias. Pairs were faster on low-complexity tasks and gave higher quality on high-complexity tasks. Hannay et al., IST 2009, https://doi.org/10.1016/j.infsof.2009.02.001 (abstract only)
- In an experiment with 295 professional consultants:
  - Overall, there was no support for less time or more correctness, and a significant 84% more effort.
  - On the complex system, pairs had 48% more correct solutions, mainly from juniors.
  - On the simple system, pairs took 20% less time, mainly intermediates and seniors.
  - Arisholm et al., IEEE TSE 2007, https://doi.org/10.1109/TSE.2007.17
- I found no controlled study of mob programming.

6. STACKED CHANGES

- At Meta, engineers send a small first commit for review and "while it's being reviewed, they will start on the next step." Sapling rebases the stack when an earlier commit changes. Goode and Bolin, Meta, 2022, https://engineering.fb.com/2022/11/15/open-source/sapling-source-control-scalable/
- Facebook "replaced [branches] with the stacked diff workflow because it made engineers more productive." One Phabricator diff is about one commit. Gabbard (ex-Facebook), 2018, https://jg.gg/2018/09/29/stacked-diffs-versus-pull-requests/
- In Gerrit, each pushed commit is its own change. A change can be based on an open change, and it lands only after its predecessors. https://gerrit-review.googlesource.com/Documentation/intro-user.html
- GitHub made native stacked PRs generally available in October 2026. Vendor claim: "over two-thirds of the top 1% of repos" use them, with "a 5% improvement in time-to-merge." https://github.blog/changelog/2026-10-06-stacked-pull-requests-generally-available/

7. AI-GENERATED CODE AND REVIEW (2024 onward)

- DORA 2025 (Google-run survey, nearly 5,000 respondents): 90% use AI at work. AI adoption now has a positive relationship with throughput and still a negative relationship with stability. 30% report little or no trust in AI code. https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
- METR ran a third-party RCT with 16 experienced OSS developers on 246 issues. With AI, the developers were 19% slower, but they believed that they were 20% faster. METR, 2025, https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- A third-party study compared 807 Cursor-adopting repositories with 1,380 matched controls.
  - Lines added went up 281.3% and commits went up 55.4% in month one. The gain was transient.
  - Static-analysis warnings went up 29.7% and code complexity went up 40.7%. These increases persisted.
  - He et al. (CMU), 2025, https://arxiv.org/abs/2511.04427
- In 456K agent PRs, agent acceptance rates were 15 to 40 percentage points below human rates (Codex 64%, Devin 49%, Copilot 35%). The data comes from about two months after the agents' release. Li, Zhang, Hassan, 2025, https://arxiv.org/abs/2507.15003
- CodeRabbit (vendor) studied 470 PRs: AI-co-authored PRs had 10.83 issues per PR against 6.45 for human-only PRs, and 75% more logic issues. Authorship was inferred, not confirmed. 2025, https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- Stripe reports "over a thousand" merged agent PRs each week, with "no human-written code", and every PR is human-reviewed.
  - Gates: deterministic lint steps, selective CI over 3M+ tests and autofixes.
  - At most two CI rounds, then the branch goes to a human.
  - The requesting engineer checks the PR first, then asks another engineer to review it.
  - Company report, 2026, https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents
- At Spotify, deterministic format, build and test verifiers block PR creation. An LLM judge then compares the diff with the prompt.
  - It vetoes "about a quarter" of sessions, and the agent corrects itself "half the time."
  - Spotify has "yet to invest in evals for our judge."
  - Company report, 2025, https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3
- Solid third-party data on review load for agent PRs is scarce. Most numbers come from vendors or from the companies themselves.

PATTERNS THE SOURCES AGREE ON

- Small changes get faster and better review: Sadowski 2018, Cisco 2006, Rigby and Bird 2013, the DORA small-batch work and Google eng-practices.
- Most review output is about maintainability and understanding, not defects: Bacchelli and Bird 2013, Beller 2014, Sadowski 2018 and the Google SWE book.
- One or two reviewers is enough: Rigby and Bird 2013 and Sadowski 2018.
- Review latency matters to delivery: DORA 2023, Google eng-practices and Sadowski 2018.
- Lighter review is acceptable only with safeguards: CI and tests, a trusted author or owner, and fast revert. The sources are Ship/Show/Ask, Fowler 2021, Apache CTR, Renovate/GitHub auto-merge and the Chromium bot for verifiably safe changes.
- External heavyweight approval gives no stability: DORA 2019. A lighter review mode found as many defects: Rigby 2008.
- Design discussion up front only when a change is ambiguous or substantial: Ubl 2020, the Rust RFC README and Shape Up.
- Higher AI code volume brings instability or quality debt: DORA 2024, DORA 2025, He et al. 2025 and CodeRabbit (vendor).
- Teams that run agents at scale put deterministic checks before human review: Stripe and Spotify.

WHERE THE SOURCES DISAGREE

- Reviewer count: Rigby and Bird say two reviewers is optimal. Google finds one sufficient, but its data shows that more reviewers give more comments.
- Post-commit review: Apache CTR (no difference in defects) and Fowler support it. Chromium removed TBR in 2021 for integrity, Google requires review even for rollbacks, and DORA says review "at check-in time".
- How much design up front: Uber wrote an RFC for anything non-trivial. Ubl calls a design doc overhead unless the design is ambiguous.
- Where design belongs: Google interviewees disagreed on whether design belongs in code review.
- AI and throughput: DORA 2024 found a negative effect, DORA 2025 a positive one, and METR found developers slower. He et al. found a gain that faded after about two months.

NOT VERIFIED

- Hannay 2009 full text and its "18 studies" count. I saw only the abstract text.
- The "+149% junior correctness" figure is in Arisholm-based course slides only, not in the abstract.
- Faros AI 2025: 98% more PRs, 91% more review time, 154% larger PRs, 9% more bugs. Its page did not show these numbers.
- Graphite, "The ideal PR is 50 lines long": the page returned 404.
- Stripe "1,300 PRs/week" (Part 2): secondary sources only.
- The Spotify QCon 2026 numbers: InfoQ only.
- Per-agent merge rates in arXiv 2607.21832: I opened only the abstract.
- McIntosh et al. 2014 (review coverage and post-release defects): I could not get the abstract.
- SmartBear's "70–90% defect discovery": it has no source on SmartBear's page.
- Definitions of spike (XP) and tracer bullet (Pragmatic Programmer): I opened no source.
- Accelerate (book, 2018): I used the DORA reports instead.