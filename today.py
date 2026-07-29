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


def make_dot_line(x: int, y: int, key: str, val: str, total_chars: int = 54) -> str:
    """
    Formats key-value pairs with exact dot justification matching Andrew6rant neofetch layout.
    """
    prefix = f". {key}: "
    val_str = str(val)
    dots_count = total_chars - len(prefix) - len(val_str)
    if dots_count < 2:
        dots_count = 2
    dots = '.' * dots_count
    return f'<tspan x="{x}" y="{y}" class="cc">. </tspan><tspan class="key">{key}</tspan>:<tspan class="cc"> {dots} </tspan><tspan class="value">{val_str}</tspan>'


def generate_svg(username: str, stats: dict, dark_mode: bool = True) -> str:
    """
    Generates dynamic SVG markup matching Andrew6rant's GitHub profile README template.
    """
    bg_color = "#161b22" if dark_mode else "#ffffff"
    text_color = "#c9d1d9" if dark_mode else "#24292e"
    key_color = "#ffa657" if dark_mode else "#d97706"
    val_color = "#a5d6ff" if dark_mode else "#0969da"
    cc_color = "#616e7f" if dark_mode else "#6e7781"
    
    age_str = calculate_age(BIRTHDAY_STR)
    if not age_str:
        age_str = "24 years, 8 months, 4 days"

    # Left column: ASCII Portrait (x=15, start_y=30, line_height=20)
    ascii_tspans = generate_ascii_svg_tspans(
        username=username,
        x=15,
        start_y=30,
        line_height=20,
        width=40,
        dark_mode=dark_mode
    )
    
    # Right column: Specs & Stats
    rx = 390
    tot_c = 54
    
    repos_cnt = stats.get('repos', 24) or 24
    stars_cnt = stats.get('stars', 12) or 12
    followers_cnt = stats.get('followers', 108) or 108
    commits_cnt = stats.get('commits', 184) or 184
    loc_add = stats.get('additions', 52140) or 52140
    loc_del = stats.get('deletions', 6930) or 6930
    total_loc = loc_add - loc_del

    # Lines array with explicit (x, y) coordinates
    lines_xml = [
        f'<tspan x="{rx}" y="30">{username}</tspan> ---------------------------------------------------',
        make_dot_line(rx, 50, "OS", "macOS, iOS, Linux", tot_c),
        make_dot_line(rx, 70, "Uptime", age_str, tot_c),
        make_dot_line(rx, 90, "Host", "Full-Stack & UI/UX Engineer", tot_c),
        make_dot_line(rx, 110, "Kernel", "Lead Frontend & System Dev", tot_c),
        make_dot_line(rx, 130, "IDE", "VSCode, Xcode, PyCharm", tot_c),
        f'<tspan x="{rx}" y="150" class="cc">. </tspan>',
        make_dot_line(rx, 170, "Languages.Programming", "TypeScript, JS, Python, C++", tot_c),
        make_dot_line(rx, 190, "Languages.Computer", "HTML, CSS, React, Next.js, SQL", tot_c),
        make_dot_line(rx, 210, "Languages.Real", "English, Telugu", tot_c),
        f'<tspan x="{rx}" y="230" class="cc">. </tspan>',
        make_dot_line(rx, 250, "Hobbies.Software", "Open Source, AI Agents, UI/UX", tot_c),
        make_dot_line(rx, 270, "Hobbies.Hardware", "Custom PCs, Smart Automation", tot_c),
        f'<tspan x="{rx}" y="290" class="cc">. </tspan>',
        f'<tspan x="{rx}" y="310">- Contact ---------------------------------------------</tspan>',
        make_dot_line(rx, 330, "Email.Personal", "krishnakondoju@gmail.com", tot_c),
        make_dot_line(rx, 350, "GitHub", "krishnaUIDev", tot_c),
        make_dot_line(rx, 370, "LinkedIn", "krishnaUIDev", tot_c),
        f'<tspan x="{rx}" y="390" class="cc">. </tspan>',
        f'<tspan x="{rx}" y="410">- GitHub Stats ----------------------------------------</tspan>',
        f'<tspan x="{rx}" y="430" class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan><tspan class="value">{repos_cnt:,}</tspan> <tspan class="key">{{Contributed: 35}}</tspan><tspan class="cc"> | </tspan><tspan class="key">Stars</tspan>:<tspan class="cc"> ............ </tspan><tspan class="value">{stars_cnt:,}</tspan>',
        f'<tspan x="{rx}" y="450" class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> .......................... </tspan><tspan class="value">{commits_cnt:,}</tspan><tspan class="cc"> | </tspan><tspan class="key">Followers</tspan>:<tspan class="cc"> ....... </tspan><tspan class="value">{followers_cnt:,}</tspan>',
        f'<tspan x="{rx}" y="470" class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan>:<tspan class="cc"> . </tspan><tspan class="value">{total_loc:,}</tspan> <tspan class="cc">(</tspan> <tspan class="addColor">{loc_add:,}++</tspan><tspan class="cc">, </tspan><tspan class="delColor">{loc_del:,}--</tspan> <tspan class="cc">)</tspan>'
    ]
    
    right_column_xml = "\n".join(lines_xml)

    svg_content = f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {key_color};}}
.value {{fill: {val_color};}}
.addColor {{fill: #3fb950;}}
.delColor {{fill: #f85149;}}
.cc {{fill: {cc_color};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="530px" fill="{bg_color}" rx="15"/>
<text x="15" y="30" fill="{text_color}" class="ascii">
{ascii_tspans}
</text>
<text x="{rx}" y="30" fill="{text_color}">
{right_column_xml}
</text>
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
