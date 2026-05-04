from backend.app import app
for rule in app.url_map.iter_rules():
    if '/api/auth/change-password' in rule.rule:
        print(rule.rule, sorted(rule.methods))
