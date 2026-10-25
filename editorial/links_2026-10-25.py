#!/usr/bin/env python3
"""One-off: add internal links, cited sources and a further-reading list to existing posts (25 October 2026).
Every external claim below was checked against the linked page on that date."""
import os, re

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "deploy", "insights")
H2 = '<h2 style="margin:18px 0 0;font-size:30px;line-height:1.15;letter-spacing:-0.02em">'

SRC = {
    "gartner26": ("https://www.gartner.com/en/newsroom/press-releases/2026-03-09-gartner-sales-survey-finds-67-percent-of-b2b-buyers-prefer-a-rep-free-experience",
                  "Gartner (2026): Sales survey finds 67% of B2B buyers prefer a rep-free experience"),
    "google": ("https://support.google.com/mail/answer/14229414?hl=en-GB", "Google: Gmail email sender guidelines FAQ"),
    "gartner20": ("https://www.gartner.com/en/newsroom/press-releases/2020-02-12-gartner-says-less-than-50--of-sales-leaders-and-selle",
                  "Gartner (2020): Less than 50% of sales leaders and sellers have high confidence in forecasting accuracy"),
    "gartner18": ("https://www.gartner.com/en/newsroom/press-releases/2018-08-08-gartner-says-b2b-buyers-want-more-simplicity-in-accessing-the-right-information-with-or-without-a-sales-rep",
                  "Gartner (2018): B2B buyers want more simplicity in accessing the right information"),
    "ebsta": ("https://ebsta.com/wp-content/uploads/2024/07/H1-Update-2024-B2B-Sales-Benchmarks.pdf", "Ebsta: H1 2024 B2B sales benchmarks (PDF)"),
    "meddicc": ("https://www.meddicc.com/meddic", "MEDDICC: What MEDDIC, MEDDICC and MEDDPICC stand for"),
    "challenger": ("https://challengerinc.com/what-is-challenger-sales-methodology/", "Challenger: What is the Challenger sales methodology?"),
    "sandler": ("https://www.salesforce.com/blog/sandler-sales-methodology/", "Salesforce: The Sandler selling system, a step-by-step guide"),
    "gong": ("https://www.gong.io/resources/labs/deal-closing-discovery-call/", "Gong Labs: What 519,000 discovery calls reveal about closing deals"),
    "saastr": ("https://www.saastr.com/the-founders-guide-to-transitioning-from-founder-led-sales-why-most-get-it-wrong-and-how-to-get-it-right",
               "SaaStr: How to transition from founder-led sales"),
    "moore": ("https://lennysnewsletter.com/p/geoffrey-moore-on-finding-your-beachhead", "Lenny's Newsletter: Geoffrey Moore on finding your beachhead"),
    "mckinsey": ("https://www.mckinsey.com/Business%20Functions/Marketing%20and%20Sales/Our%20Insights/The%20power%20of%20pricing", "McKinsey Quarterly (2003): The power of pricing"),
    "batna": ("https://en.wikipedia.org/wiki/Best_alternative_to_a_negotiated_agreement", "Wikipedia: Best alternative to a negotiated agreement (BATNA)"),
    "pon": ("https://www.pon.harvard.edu/daily/negotiation-skills-daily/when-to-make-the-first-offer-in-negotiation",
            "Harvard Program on Negotiation: When to make the first offer in negotiation"),
}


def x(key, text):
    return f'<a href="{SRC[key][0]}" target="_blank" rel="noopener">{text}</a>'


def i(pid, text):
    return f'<a href="/insights/{pid}">{text}</a>'


EDITS = {
    "ai-sdrs": [
        ("buyers learn to ignore all of them.",
         f"buyers learn to ignore all of them. Many would rather skip sellers entirely: in Gartner's 2026 survey, {x('gartner26', '67 percent of B2B buyers said they prefer a rep-free buying experience')}."),
        ("is exactly the pattern spam filters are designed to catch.",
         f"is exactly the pattern spam filters are designed to catch. Google's {x('google', 'sender guidelines')} ask senders to keep reported spam below 0.1 percent and never reach 0.3 percent."),
        ("Improve conversion to qualified pipeline,", f"Improve conversion to {i('pipeline-coverage', 'qualified pipeline')},"),
        ("and hold them to a quality bar: meetings that turn into real opportunities.",
         f"and hold them to a quality bar: meetings that turn into real opportunities. There is a practical weekly rhythm for this in {i('signal-over-noise', 'the contract between buyers and sellers is broken')}."),
    ],
    "cold-email-senior-buyers": [
        ("and they ask for very little.",
         f"and they ask for very little. The bar keeps rising: in Gartner's 2026 survey, {x('gartner26', '67 percent of B2B buyers said they prefer a rep-free buying experience')}, so an email has to earn the conversation."),
        ("a handwritten card", i("signal-over-noise", "a handwritten card")),
        ("change the angle rather than the volume.",
         f"change the angle rather than the volume. Volume also carries a cost: Google's {x('google', 'sender guidelines')} ask senders to keep reported spam below 0.1 percent, and every ignored, generic email makes that harder."),
        ("will usually outperform a large number of generic ones.",
         f"will usually outperform a large number of generic ones. When someone does reply, the next job is {i('discovery-call', 'a first call that earns the second meeting')}."),
    ],
    "discovery-call": [
        ("The detail is where the value is.",
         f"The detail is where the value is. Gong's analysis of 519,000 recorded discovery calls found that the most successful ones explored three or four business problems in depth and involved {x('gong', '11 to 14 questions')}, spread across the call rather than front-loaded."),
        ("You need enough to know whether the opportunity is real and who to meet next.",
         f"You need enough to know whether the opportunity is real and who to meet next. Frameworks such as {x('meddicc', 'MEDDPICC')} give these questions a structure: the economic buyer, decision criteria, decision process and paper process all start here, and the paper process is where {i('working-with-procurement', 'procurement')} comes in."),
        ("Save the demo for a later meeting, built around what you learned.",
         "Save the demo for a later meeting, built around what you learned. In the same Gong research, the strongest calls had frequent back-and-forth between buyer and seller, closer to a conversation than a presentation."),
        ("the starting point for the mutual success plan", f"the starting point for the {i('mutual-success-plans', 'mutual success plan')}"),
    ],
    "first-sales-playbook": [
        ("Frameworks like MEDDPICC, Sandler and Challenger exist because they work.",
         f"Frameworks like {x('meddicc', 'MEDDPICC')}, {x('sandler', 'Sandler')} and {x('challenger', 'Challenger')} exist because they work."),
        ("Be specific enough that a seller can rule an account out.",
         f"Be specific enough that a seller can rule an account out. If the list points to several groups, {i('pick-one-segment', 'pick one segment and win it first')}."),
        ("is evidence. Every stage needs a clear test for moving on.",
         f"is evidence. Every stage needs a clear test for moving on. There is more on this in {i('forecast-evidence', 'a forecast is evidence, not optimism')}."),
        ("With a playbook in place, hiring gets easier.",
         f"With a playbook in place, hiring gets easier, and you can {i('founder-led-sales-handoff', 'hand off deals in stages')} rather than all at once."),
    ],
    "forecast-evidence": [
        ("It needs discipline about what counts as proof.",
         f"It needs discipline about what counts as proof. The problem is widespread: in Gartner's State of Sales Operations survey, {x('gartner20', 'only 45 percent of sales leaders and sellers')} said they had high confidence in their organisation's forecast accuracy."),
        ("the buyer has agreed a mutual success plan with named owners", f"the buyer has agreed a {i('mutual-success-plans', 'mutual success plan')} with named owners"),
        ("Track how accurate each seller's commit calls are over time.",
         f"Track how accurate each seller's commit calls are over time, and use the categories to keep {i('weekly-forecast-call', 'the weekly forecast call')} short."),
        ("how much pipeline you have against target,", f"how much {i('pipeline-coverage', 'pipeline you have against target')},"),
        ("usually weeks before the number misses.",
         f"usually weeks before the number misses. Slippage is more common than most teams assume: {x('ebsta', 'Ebsta’s 2024 benchmark data')} found that between 34 and 46 percent of deals slipped past their close date each quarter in the first half of that year."),
    ],
    "founder-led-sales-handoff": [
        ("you will pay a leadership salary for individual work.</p>",
         f"you will pay a leadership salary for individual work.</p>\n<p>Not everyone agrees on timing. {x('saastr', 'SaaStr’s guide to the transition')} argues founders should stay hands-on for much longer, in some cases until around $10M in annual recurring revenue, with a few account executives first and a head of sales later. The common ground is the sequence: sellers before a sales leader, and the founder still in the most important deals.</p>"),
        ("The weekly deal review, where", f"The weekly {i('forecast-evidence', 'deal review')}, where"),
    ],
    "mutual-success-plans": [
        ("The deal closed two quarters later, or never.",
         f"The deal closed two quarters later, or never. It is a common story: {x('ebsta', 'Ebsta’s 2024 benchmarks')} found that between 34 and 46 percent of deals slipped past their close date each quarter in the first half of that year."),
        ("The answers will tell you more about the deal than any discovery call.",
         f"The answers will tell you more about the deal than any {i('discovery-call', 'discovery call')}. Gartner has described the B2B buying journey as {x('gartner18', 'close to unnavigable without significant help')}, and a plan built together is exactly that help."),
        ("Legal and procurement, including redlines on your contract", f"Legal and {i('working-with-procurement', 'procurement')}, including redlines on your contract"),
        ("Ask them to find out, and put that on the plan too.",
         f"Ask them to find out, and put that on the plan too. The {x('meddicc', 'MEDDPICC')} framework calls this the paper process: every step between a buyer saying yes and a signed contract."),
        ("That makes the plan one of the best forecasting tools you have.",
         f"That makes the plan one of the best {i('forecast-evidence', 'forecasting tools')} you have."),
    ],
    "pick-one-segment": [
        ("The fix is to choose one segment and become the obvious choice for it before you expand.",
         f"The fix is to choose one segment and become the obvious choice for it before you expand. Geoffrey Moore made the same case in Crossing the Chasm, describing a good beachhead as {x('moore', '“big enough to matter, small enough to lead”')} and a good fit with what you do best."),
        ("at a realistic win rate,", f"at a {i('pipeline-coverage', 'realistic win rate')},"),
        ("Pointing outbound and events at named accounts within it.", f"Pointing {i('signal-over-noise', 'outbound and events')} at named accounts within it."),
        ("new sellers can ramp on it without the founder's help.", f"new sellers can ramp on it {i('founder-led-sales-handoff', 'without the founder’s help')}."),
    ],
    "pipeline-coverage": [
        ("That is your real coverage ratio.",
         f"That is your real coverage ratio. Benchmarks move, which is why your own numbers matter more: {x('ebsta', 'Ebsta’s 2024 data')} showed win rates down 7 percent on the previous year while total pipeline grew 25 percent, exactly the kind of shift a fixed rule of thumb misses."),
        ("Create more pipeline. It is the slowest", f"Create more pipeline, ideally through {i('signal-over-noise', 'outreach buyers actually read')}. It is the slowest"),
        ("with better deal reviews, mutual success plans and executive involvement.",
         f"with better {i('forecast-evidence', 'deal reviews')}, {i('mutual-success-plans', 'mutual success plans')} and executive involvement."),
        ("Increase deal size through multi-year terms,", f"Increase deal size through multi-year terms ({i('stop-discounting', 'a good trade for any discount')}),"),
    ],
    "signal-over-noise": [
        ("Domains get flagged, so they buy more domains.",
         f"Domains get flagged, so they buy more domains, while mailbox providers tighten the rules: Google's {x('google', 'sender guidelines')} ask senders to keep reported spam below 0.1 percent."),
        ("send those five insights by email or LinkedIn,", f"send those five insights {i('cold-email-senior-buyers', 'by email')} or LinkedIn,"),
        ("I am not arguing against technology.", f"I am not arguing against technology, though I am sceptical of {i('ai-sdrs', 'AI SDRs')} in enterprise sales."),
        ("Buyers have not stopped buying.",
         f"Buyers have not stopped buying. They are doing more of it on their own: in Gartner's 2026 survey, {x('gartner26', '67 percent of B2B buyers said they prefer a rep-free buying experience')}, and 45 percent had used AI during a recent purchase."),
    ],
    "stop-discounting": [
        ("and they signal that your price was never real.",
         f"and they signal that your price was never real. Price is also the strongest profit lever most companies have: a {x('mckinsey', 'McKinsey analysis')} of the average S&amp;P 1500 company estimated that a 1 percent price increase, with volume held steady, would lift operating profit by about 8 percent. Discounts work the same way in reverse."),
        ("The weaker their alternative, the stronger your position.",
         f"The weaker their alternative, the stronger your position. Negotiators call this the {x('batna', 'BATNA')}, the best alternative to a negotiated agreement."),
        ("price becomes one part of a bigger conversation.",
         f"price becomes one part of a bigger conversation. Research summarised by the {x('pon', 'Harvard Program on Negotiation')} shows how strongly the first number anchors everything after it, so make sure the first number discussed is the cost of the problem, not your discount."),
        ("agreed in the mutual success plan.", f"agreed in the {i('mutual-success-plans', 'mutual success plan')}."),
        ("Surface procurement, legal and security early", f"Surface {i('working-with-procurement', 'procurement')}, legal and security early"),
        ("Keep enough pipeline that no single deal", f"Keep {i('pipeline-coverage', 'enough pipeline')} that no single deal"),
    ],
    "weekly-forecast-call": [
        ("and the real problems in the pipeline go unnoticed.",
         f"and the real problems in the pipeline go unnoticed. It shows in the results: in Gartner's State of Sales Operations survey, {x('gartner20', 'only 45 percent of sales leaders and sellers')} had high confidence in their forecast accuracy."),
        ("a category (commit, best case or pipeline)", f"a category ({i('forecast-evidence', 'commit, best case or pipeline')})"),
        ("A deal that slips should come with a reason.",
         f"A deal that slips should come with a reason. Plan for slippage: {x('ebsta', 'Ebsta’s 2024 benchmarks')} found that a third or more of deals slipped past their close date each quarter in the first half of that year."),
        ("a quick look at coverage for the following period.", f"a quick look at {i('pipeline-coverage', 'coverage')} for the following period."),
    ],
    "working-with-procurement": [
        ("It removes most late surprises.",
         f"It removes most late surprises. The {x('meddicc', 'MEDDPICC')} framework calls this the paper process: every step between a verbal yes and a signed contract."),
        ("Add each answer to the mutual success plan", f"Add each answer to the {i('mutual-success-plans', 'mutual success plan')}"),
        ("Know your walk-away position,", f"Know your walk-away position (which depends on your {x('batna', 'BATNA')}, your best alternative if this deal falls through),"),
        ("Trade every concession for something.", f"{i('stop-discounting', 'Trade every concession')} for something."),
    ],
}


def run():
    for pid, edits in EDITS.items():
        path = os.path.join(D, pid + ".html")
        s = open(path, encoding="utf-8").read()
        if "Sources and further reading" in s:
            print("skip (already done)", pid)
            continue
        m = re.search(r'(  <sc-if value="\{\{ p\d+ \}\}"[^>]*>\n    <div style="display:grid;gap:22px">\n)(.*?)(\n    </div>\n  </sc-if>)', s, re.S)
        body = m.group(2)
        for old, new in edits:
            n = body.count(old)
            assert n == 1, f"{pid}: {n} matches for {old!r}"
            body = body.replace(old, new)
        used = []
        for url in re.findall(r'<a href="(https://[^"]+)"', body):
            if url not in used:
                used.append(url)
        label = {v[0]: v[1] for v in SRC.values()}
        items = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{label[u]}</a></li>' for u in used)
        refs = f'\n    {H2}Sources and further reading</h2>\n    <ul style="padding-left:22px">{items}</ul>'
        if "Frequently asked questions</h2>" in body:  # keep FAQ last
            body = body.replace(f"\n    {H2}Frequently asked questions</h2>", refs + f"\n    {H2}Frequently asked questions</h2>", 1)
        else:
            body += refs
        s = s[:m.start(2)] + body + s[m.end(2):]
        open(path, "w", encoding="utf-8").write(s)
        print("ok", pid, len(edits), "edits,", len(used), "sources")


if __name__ == "__main__":
    run()
