import json
results = json.load(open('results/federal_axe_violations.json'))

violation_counts = results['violation_counts']


sorted_counts = sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)

print(sorted_counts[:10])


