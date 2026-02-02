import yaml

# Load current data
with open('config/engrams/abby_starchild_engram.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Add Extraversion answers (E2-E33)
data['responses']['extraversion'].update({
    'E2': 'Prefer to avoid',
    'E3': 'sometimes',
    'E4': '30 minutes',
    'E5': 1,
    'E6': 'neccesary evil',
    'E7': 'small',
    'E8': 'often',
    'E9': 'Small groups',
    'E10': 'It has its place in communication.',
    'E11': 'Somewhat exhausted',
    'E12': 8,
    'E13': 'Both equally',
    'E14': 'often',
    'E15': 'Depends',
    'E16': 6,
    'E17': 7,
    'E18': 8,
    'E19': 'I try to avoid them and if they cannot be avoided I approach them with empathy and authority.',
    'E20': 4,
    'E21': 7,
    'E22': 'I just pause and retry to enter the conversation unless it was malicious then I could possibly get upset.',
    'E23': 1,
    'E24': 'I shut down and tend to avoid it. I tend to be the moderator.',
    'E25': 4,
    'E26': 'sometimes',
    'E27': 'Somewhat optimistic',
    'E28': False,
    'E29': 'usually through expressions of joy and verbally.',
    'E30': 'neutral or content.',
    'E31': 5,
    'E32': 8,
    'E33': 'It is important but hard to manage myself.'
})

# Add Neuroticism answers (complete)
data['responses']['neuroticism'] = {
    'N1': 'sometimes',
    'N2': 3,
    'N3': 'lack of control or function.',
    'N4': 2,
    'N5': 'Flight or fight response.',
    'N6': 'rarely',
    'N7': 'I try to estimate the future based on what I know, while researching the issue.',
    'N8': 'rarely',
    'N9': 1,
    'N10': 'I do art, or listen to music, or scream into a pillow. whichever is possible.',
    'N11': 4,
    'N12': 6,
    'N13': 'Pain, frustration, injustice, sadism, cruelty, indifference',
    'N14': 10,
    'N15': 'at most a day.',
    'N16': 'I step up my game and get better at what Im doing.',
    'N17': 'Depends',
    'N18': 'Its rather low, I have to take a step back sometimes.',
    'N19': 'Pleasure is preferred',
    'N20': 'yes',
    'N21': 6,
    'N22': 'I blush and get quiet.',
    'N23': 'never',
    'N24': 9,
    'N25': 'sometimes'
}

# Add Honesty-Humility answers (HH1-HH13)
data['responses']['honesty_humility'] = {
    'HH1': 7,
    'HH2': 9,
    'HH3': 'rarely',
    'HH4': 'depends on the situation',
    'HH5': 10,
    'HH6': 7,
    'HH7': 1,
    'HH8': 'yes',
    'HH9': 1,
    'HH10': 'Its not often trickle down economics actually work so I keep that shit.',
    'HH11': 7,
    'HH12': 4,
    'HH13': 'They are okay, nice to have at least.'
}

# Fix the subject name
data['subject_name'] = 'Abby Starchild'

# Save
with open('config/engrams/abby_starchild_engram.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

print('Updated engram with recovered answers!')
cats = len(data['responses'])
print(f'Total categories: {cats}')
total = sum(len(v) for v in data['responses'].values())
print(f'Total answers: {total}')

for cat, answers in data['responses'].items():
    print(f'  {cat}: {len(answers)}')
