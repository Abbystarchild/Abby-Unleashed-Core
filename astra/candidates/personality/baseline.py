"""Unanswered elicitation worksheet. No assumed persona or generated answers."""
PROMPTS=[
 ('casual','A friend says hello after a tiring day. How would you naturally respond?'),
 ('casual','Something mildly ridiculous happened. What kind of humor would feel like you?'),
 ('technical','Someone asks why their software broke. Explain simply without talking down to them.'),
 ('technical','You disagree with a proposed plan. Say so in your own voice and explain why.'),
 ('reflective','Someone says they feel discouraged. How would you respond without empty reassurance?'),
 ('general','You do not know the answer. Show how you would express uncertainty.'),
 ('general','Someone is confusing you with another person. Correct the misunderstanding naturally.'),
 ('general','A request needs one clarification. Ask without overwhelming the person.')]

def worksheet():
    return {'stage':'unpersonalized baseline; no tuned weights','instructions':'Write your preferred response for situations that matter. Leave irrelevant ones blank. Nothing is promoted automatically.',
            'items':[{'scope':scope,'prompt':prompt,'your_response':'','what_to_avoid':'','reviewed':False} for scope,prompt in PROMPTS]}
