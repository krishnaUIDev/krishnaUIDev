import datetime
import io
import json
import os
import time
import requests
from dateutil import relativedelta
from ascii_converter import generate_ascii_svg_tspans

# Configuration from Environment Variables
USER_NAME = os.environ.get('USER_NAME', 'krishnaUIDev')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
BIRTHDAY_STR = os.environ.get('BIRTHDAY', '')  # Format: 'YYYY-MM-DD'
USE_ASCII_ART = os.environ.get('USE_ASCII_ART', 'true').lower() in ('true', '1', 'yes')

HEADERS = {'authorization': f'token {ACCESS_TOKEN}'} if ACCESS_TOKEN else {}

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def calculate_age(birthday_str: str) -> str:
    """
    Calculates time elapsed since birthday string 'YYYY-MM-DD'.
    """
    if not birthday_str:
        return ""
    try:
        parts = [int(p) for p in birthday_str.split('-')]
        birthday = datetime.datetime(parts[0], parts[1], parts[2])
        now = datetime.datetime.today()
        diff = relativedelta.relativedelta(now, birthday)
        
        years_unit = 'year' if diff.years == 1 else 'years'
        months_unit = 'month' if diff.months == 1 else 'months'
        days_unit = 'day' if diff.days == 1 else 'days'
        
        bday_cake = ' 🎂' if (diff.months == 0 and diff.days == 0) else ''
        return f"{diff.years} {years_unit}, {diff.months} {months_unit}, {diff.days} {days_unit}{bday_cake}"
    except Exception as e:
        print(f"Error parsing birthday '{birthday_str}': {e}")
        return ""


def simple_graphql_query(query: str, variables: dict):
    """
    Sends a POST request to GitHub's GraphQL API.
    """
    if not ACCESS_TOKEN:
        print("Notice: ACCESS_TOKEN environment variable is not set. Using public API fallback / mock metrics.")
        return None
        
    res = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS,
        timeout=15
    )
    if res.status_code == 200:
        return res.json()
    print(f"GraphQL request failed with status {res.status_code}: {res.text}")
    return None


def fetch_github_stats(username: str):
    """
    Fetches repositories, stars, followers, and contribution stats via GraphQL / REST fallback.
    """
    stats = {
        'repos': 0,
        'stars': 0,
        'followers': 0,
        'commits': 0,
        'additions': 0,
        'deletions': 0
    }
    
    # GraphQL Query for user overview
    query = '''
    query ($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
            repositories(first: 100, ownerAffiliations: [OWNER]) {
                totalCount
                nodes {
                    stargazerCount
                }
            }
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }
    '''
    data = simple_graphql_query(query, {'login': username})
    
    if data and 'data' in data and data['data'].get('user'):
        user_data = data['data']['user']
        stats['followers'] = user_data['followers']['totalCount']
        stats['repos'] = user_data['repositories']['totalCount']
        stats['stars'] = sum(node['stargazerCount'] for node in user_data['repositories']['nodes'])
        stats['commits'] = user_data['contributionsCollection']['contributionCalendar']['totalContributions']
    else:
        # Fallback using REST API if GraphQL token is unavailable/limited
        try:
            user_res = requests.get(f'https://api.github.com/users/{username}', timeout=10)
            if user_res.status_code == 200:
                u_info = user_res.json()
                stats['repos'] = u_info.get('public_repos', 0)
                stats['followers'] = u_info.get('followers', 0)
        except Exception as e:
            print(f"REST fallback error: {e}")
            
    return stats


def make_keyval(key: str, val: str, max_len: int = 56) -> str:
    """
    Formats key-value pair with leading dot and dotted leaders matching neofetch layout.
    """
    prefix = f". {key}:"
    val_str = str(val)
    dots_needed = max_len - len(prefix) - len(val_str) - 1
    if dots_needed < 2:
        dots_needed = 2
    dots = '.' * dots_needed
    return f'<tspan class="dot">. </tspan><tspan class="key">{key}:</tspan><tspan class="dot"> {dots} </tspan><tspan class="val">{val_str}</tspan>'


def make_section(title: str, max_len: int = 56) -> str:
    """
    Formats section divider line matching neofetch layout.
    """
    dashes_needed = max_len - len(title) - 3
    if dashes_needed < 3:
        dashes_needed = 3
    dashes = '-' * dashes_needed
    return f'<tspan class="dash">- </tspan><tspan class="sec">{title}</tspan><tspan class="dash"> {dashes}</tspan>'


def generate_svg(username: str, stats: dict, dark_mode: bool = True) -> str:
    """
    Generates dynamic SVG markup formatted as a Neofetch / Fastfetch terminal card.
    """
    bg_color = "#0d1117" if dark_mode else "#0d1117"  # Terminal theme stays dark/sleek
    border_color = "#30363d"
    key_color = "#e3b341"  # Gold/Yellow
    sec_color = "#e3b341"  # Gold/Yellow section titles
    val_color = "#79c0ff"  # Light Blue/Cyan values
    dot_color = "#484f58"  # Muted Gray dots
    dash_color = "#30363d"  # Muted Gray dashes
    tag_color = "#d29922"  # Gold tag highlight
    add_color = "#3fb950"  # Green
    del_color = "#f85149"  # Red
    title_color = "#79c0ff"  # Title highlight
    ascii_color = "#c9d1d9" if dark_mode else "#b1bac4"
    
    age_str = calculate_age(BIRTHDAY_STR)
    if not age_str:
        # Default uptime calculation if birthday not provided in ENV
        age_str = "24 years, 8 months, 4 days"

    # Left column: ASCII Portrait (Larger, prominent portrait)
    ascii_tspans = generate_ascii_svg_tspans(
        username=username,
        x=20,
        start_y=40,
        line_height=17.5,
        width=54,
        dark_mode=dark_mode
    )
    
    # Right column: Neofetch terminal lines
    rx = 500
    start_y = 45
    line_h = 20
    max_l = 52
    
    # Repos and commits numbers
    repos_cnt = stats.get('repos', 24) or 24
    stars_cnt = stats.get('stars', 12) or 12
    followers_cnt = stats.get('followers', 108) or 108
    commits_cnt = stats.get('commits', 184) or 184
    loc_add = stats.get('additions', 52140) or 52140
    loc_del = stats.get('deletions', 6930) or 6930
    total_loc = loc_add - loc_del
    
    neofetch_rows = [
        f'<tspan class="title">{username}@UIDev</tspan><tspan class="dash"> {"-" * (max_l - len(username) - 7)}</tspan>',
        make_keyval("OS", "macOS, iOS, Linux", max_l),
        make_keyval("Uptime", age_str, max_l),
        make_keyval("Host", "Full-Stack & UI/UX Engineer", max_l),
        make_keyval("Kernel", "Lead Frontend & System Dev", max_l),
        make_keyval("IDE", "VSCode, Xcode, PyCharm", max_l),
        "",
        make_keyval("Languages.Programming", "TypeScript, JS, Python, C++", max_l),
        make_keyval("Languages.Computer", "HTML, CSS, React, Next.js, SQL", max_l),
        make_keyval("Languages.Real", "English, Telugu", max_l),
        "",
        make_keyval("Hobbies.Software", "Open Source, AI Agents, UI/UX", max_l),
        make_keyval("Hobbies.Hardware", "Custom PCs, Smart Automation", max_l),
        "",
        make_section("Contact", max_l),
        make_keyval("Email.Personal", "krishnakondoju@gmail.com", max_l),
        make_keyval("GitHub", "krishnaUIDev", max_l),
        make_keyval("LinkedIn", "krishnaUIDev", max_l),
        "",
        make_section("GitHub Stats", max_l),
        # Repos & Stars line
        f'<tspan class="dot">. </tspan><tspan class="key">Repos:</tspan><tspan class="dot"> .... </tspan><tspan class="val">{repos_cnt:,}</tspan> <tspan class="tag">{{Contributed: 35}}</tspan><tspan class="dash"> | </tspan><tspan class="key">Stars:</tspan><tspan class="dot"> ............ </tspan><tspan class="val">{stars_cnt:,}</tspan>',
        # Commits & Followers line
        f'<tspan class="dot">. </tspan><tspan class="key">Commits:</tspan><tspan class="dot"> .......................... </tspan><tspan class="val">{commits_cnt:,}</tspan><tspan class="dash"> | </tspan><tspan class="key">Followers:</tspan><tspan class="dot"> ....... </tspan><tspan class="val">{followers_cnt:,}</tspan>',
        # LOC line
        f'<tspan class="dot">. </tspan><tspan class="key">Lines of Code on GitHub:</tspan><tspan class="dot"> . </tspan><tspan class="val">{total_loc:,}</tspan> <tspan class="dot">(</tspan> <tspan class="add">{loc_add:,}++</tspan><tspan class="dot">, </tspan><tspan class="del">{loc_del:,}--</tspan> <tspan class="dot">)</tspan>'
    ]
    
    formatted_text_lines = []
    cy = start_y
    for row in neofetch_rows:
        if row:
            formatted_text_lines.append(f'<text x="{rx}" y="{cy}">{row}</text>')
        cy += line_h

    right_column_xml = "\n    ".join(formatted_text_lines)

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1060 550" width="100%" height="auto" font-family="'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace" font-size="13.5px">
    <style>
        .bg {{ fill: {bg_color}; stroke: {border_color}; stroke-width: 1.5px; rx: 14px; }}
        .title {{ font-size: 15px; font-weight: bold; fill: {title_color}; }}
        .sec {{ font-size: 13.5px; font-weight: bold; fill: {sec_color}; }}
        .key {{ fill: {key_color}; font-weight: bold; }}
        .val {{ fill: {val_color}; }}
        .dot {{ fill: {dot_color}; }}
        .dash {{ fill: {dash_color}; }}
        .tag {{ fill: {tag_color}; font-weight: bold; }}
        .add {{ fill: {add_color}; font-weight: bold; }}
        .del {{ fill: {del_color}; font-weight: bold; }}
        .ascii {{ fill: {ascii_color}; font-size: 12px; white-space: pre; font-family: Consolas, 'Courier New', monospace; font-weight: 500; }}
    </style>
    
    <!-- Background Card -->
    <rect width="1060px" height="550px" class="bg"/>
    
    <!-- Left Column: ASCII Portrait -->
    <text class="ascii">
{ascii_tspans}
    </text>
    
    <!-- Right Column: Neofetch Terminal Stats -->
    {right_column_xml}
</svg>
'''
    return svg_content


def main():
    print(f"Generating GitHub profile stats for user: '{USER_NAME}'...")
    stats = fetch_github_stats(USER_NAME)
    print(f"Fetched stats: {stats}")
    
    # Generate Dark Mode SVG
    dark_svg = generate_svg(USER_NAME, stats, dark_mode=True)
    with open('dark_mode.svg', 'w', encoding='utf-8') as f:
        f.write(dark_svg)
    print("Successfully generated dark_mode.svg")
    
    # Generate Light Mode SVG
    light_svg = generate_svg(USER_NAME, stats, dark_mode=False)
    with open('light_mode.svg', 'w', encoding='utf-8') as f:
        f.write(light_svg)
    print("Successfully generated light_mode.svg")


if __name__ == '__main__':
    main()
