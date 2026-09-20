def risk(p):
    if p>=.80:return "Low Risk"
    if p>=.60:return "Medium Risk"
    return "High Risk"

def pct(p): return round(p*100,2)

def winner_insight(home,away,f,p):
    lead="Home advantage" if f["home_form5"]>=f["away_form5"] else "Recent form"
    return f"{lead} gives {home} a measurable edge over {away} in the current feature set — {p['double_chance']} is the model's safer outcome."

def goals_insight(home,away,f,p):
    avg=f["home_gf5"]+f["away_gf5"]; side="goal-friendly" if avg>=2.4 else "more controlled"
    return f"Recent scoring averages point to a {side} profile: {home} {f['home_gf5']:.1f} GF/5 and {away} {f['away_gf5']:.1f} GF/5."

def corners_insight(home,away,f,p):
    return f"Corner projection: {p['projection']:.1f} total — {home} ({f['home_corners']:.1f} avg) vs {away} ({f['away_corners']:.1f} avg)."
