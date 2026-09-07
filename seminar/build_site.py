import os
import json
import re
from datetime import datetime

ORGANIZERS_BY_YEAR = {
    "2024-2025": "Chris Brav",
    "2025-2026": "Chris Brav, Aron Heleodoro",
    "2026-2027": "Emile Bouaziz, Chris Brav, Aron Heleodoro"
}
TODAY = datetime(2026, 9, 4)

def get_academic_year(date_obj):
    if date_obj.month >= 7: return f"{date_obj.year}-{date_obj.year + 1}"
    return f"{date_obj.year - 1}-{date_obj.year}"

def get_fudan_term(date_obj):
    mmdd = date_obj.month * 100 + date_obj.day
    if 830 <= mmdd or mmdd <= 109: return "Fall Semester"
    elif 110 <= mmdd <= 213: return "Winter Break"
    elif 214 <= mmdd <= 626: return "Spring Semester"
    else: return "Summer (Special Meeting)"

def format_date_line(date_obj):
    if date_obj == datetime.max: return "TBD"
    return date_obj.strftime('%A, %b %d, %Y')

def format_time_line(time_str):
    match = re.search(r'(\d{1,2}(?::\d{2})?)\s*[-~\u2013]\s*(\d{1,2}(?::\d{2})?)', time_str)
    if not match: return time_str
    norm = lambda t: t if ':' in t else f"{t}:00"
    return f"{norm(match.group(1))} - {norm(match.group(2))}"

def format_location_line(venue):
    # extract the room number, ignoring the rest of the address/Zoom details
    match = re.search(r'(?:Room\s*)?R?(\d{3,4})', venue) if venue else None
    if match: return f"Room {match.group(1)}, SIMIS"
    return venue if venue else "TBD"

def build_site():
    if not os.path.exists('seminars.json'): return
        
    with open('seminars.json', 'r', encoding='utf-8') as f:
        seminars = json.load(f)
        
    for s in seminars:
        if s.get('date'):
            s['dt'] = datetime.strptime(s['date'], '%Y-%m-%d')
            s['ay'] = get_academic_year(s['dt'])
            s['term'] = get_fudan_term(s['dt'])
            s['status'] = "Upcoming" if s['dt'] >= TODAY else "Past"
        else:
            s['dt'] = datetime.max
            s['ay'] = "2026-2027" 
            s['term'] = "TBD"
            s['status'] = "Upcoming"

    seminars.sort(key=lambda x: x['dt'], reverse=True)
    
    ay_groups = {"2026-2027": [], "2025-2026": [], "2024-2025": []}
    for s in seminars:
        if s['ay'] not in ay_groups: ay_groups[s['ay']] = []
        ay_groups[s['ay']].append(s)

    os.makedirs("seminar_website", exist_ok=True)
    
    base_css = """
    <style>
        :root { --primary: #004d99; --text: #333; --bg: #f9f9f9; --affil: #777; }
        body { font-family: -apple-system, system-ui, sans-serif; margin: 0; color: var(--text); line-height: 1.6; }
        header { background: var(--primary); color: white; padding: 20px 40px; }
        .container { display: flex; max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .sidebar { width: 250px; padding-right: 40px; border-right: 1px solid #e0e0e0; }
        .sidebar h3 { font-size: 1.1rem; border-bottom: 2px solid var(--primary); padding-bottom: 5px; margin-top: 0; }
        .sidebar h3.archive-heading { margin-top: 30px; }
        .sidebar ul { list-style: none; padding: 0; }
        .sidebar li { margin-bottom: 10px; }
        .main-content { flex: 1; padding-left: 40px; }
        .seminar-row { display: flex; border-bottom: 1px solid #e0e0e0; padding: 15px 0; }
        .seminar-date { width: 160px; font-weight: 600; color: #555; font-size: 0.9em; }
        .seminar-details { flex: 1; }
        .speaker-name { font-weight: 600; margin-bottom: 3px; }
        .affiliation { color: var(--affil); font-weight: normal; font-size: 0.9em; margin-left: 5px; }
        .term-header { margin-top: 40px; border-bottom: 2px solid var(--primary); font-size: 1.2em; color: var(--primary); }
    </style>
    """

    mathjax = "<script>MathJax = { tex: { inlineMath: [['$', '$']] } };</script><script async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>"

    for ay, talks in ay_groups.items():
        page_name = "index.html" if ay == "2026-2027" else f"archive_{ay.replace('-','_')}.html"
        current_organizers = ORGANIZERS_BY_YEAR.get(ay, "TBD")
        
        sidebar = "<h3>Current</h3><ul>"
        sidebar += "<li><a href='index.html'>2026-2027</a></li></ul>"
        sidebar += "<h3 class='archive-heading'>Archives</h3><ul>"
        sidebar += "<li><a href='archive_2025_2026.html'>2025-2026</a></li>"
        sidebar += "<li><a href='archive_2024_2025.html'>2024-2025</a></li></ul>"
        sidebar += f"<div style='margin-top: 30px; font-size:0.9em; color:#666;'><strong>Organizers:</strong><br>{current_organizers}</div>"

        html_content = ""
        current_term = None
        
        for s in talks:
            if s['term'] != current_term:
                current_term = s['term']
                html_content += f"<div class='term-header'>{current_term}</div>"
            
            date_str = s['dt'].strftime('%b %d, %Y') if s['dt'] != datetime.max else "TBD"
            affil_html = f"<span class='affiliation'>({s['affiliation']})</span>" if s['affiliation'] else ""
            
            html_content += f"""
            <div class="seminar-row">
                <div class="seminar-date">{date_str}<br><span style="font-size:0.85em; font-weight:normal; color:#888;">{s['status']}</span></div>
                <div class="seminar-details">
                    <div class="speaker-name">{s['speaker']} {affil_html}</div>
                    <div style="font-style: italic;"><a href="{s['id']}.html" style="color:var(--primary); text-decoration:none;">{s['title']}</a></div>
                </div>
            </div>
            """
            
            if s['id'] != "TBD":
                # Added <meta charset="UTF-8"> to the head
                talk_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{s['title']}</title>{base_css}{mathjax}</head><body style='padding:40px; max-width:800px; margin:auto;'>"
                date_line = format_date_line(s['dt'])
                time_line = format_time_line(s['time'])
                location_line = format_location_line(s['venue'])
                talk_html += f"<a href='{page_name}'>← Back</a><h1>{s['title']}</h1><p><strong>Speaker:</strong> {s['speaker']} {affil_html}</p><p><strong>Date:</strong> {date_line}</p><p><strong>Time:</strong> {time_line} (with a 15 min break for tea in the middle)</p><p><strong>Location:</strong> {location_line}</p><h3>Abstract</h3><div>{s['abstract']}</div></body></html>"
                
                # Added encoding='utf-8' to open()
                with open(os.path.join("seminar_website", f"{s['id']}.html"), 'w', encoding='utf-8') as f:
                    f.write(talk_html)

        if not talks:
            html_content = "<p style='margin-top: 20px; color: #666;'><em>No seminars scheduled yet. Please check the archives for past events.</em></p>"

        # Added <meta charset="UTF-8"> to the head
        page_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{ay} Seminars</title>{base_css}{mathjax}</head><body><header><h1>SIMIS Derived and Noncommutative Geometry</h1></header><div class='container'><aside class='sidebar'>{sidebar}</aside><main class='main-content'><h2>Academic Year {ay}</h2>{html_content}</main></div></body></html>"
        
        # Added encoding='utf-8' to open()
        with open(os.path.join("seminar_website", page_name), 'w', encoding='utf-8') as f:
            f.write(page_html)

if __name__ == "__main__":
    build_site()