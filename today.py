import datetime
import io
import json
import os
import time
import requests
from dateutil import relativedelta
from ascii_converter import generate_ascii_svg_tspans

# Configuration from Environment Variables
USER_NAME = os.environ.get('USER_NAME', 'krishnakondoju')
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


def generate_svg(username: str, stats: dict, dark_mode: bool = True) -> str:
    """
    Generates dynamic SVG markup with custom themes (dark/light) and ASCII profile portrait.
    """
    bg_color = "#0d1117" if dark_mode else "#ffffff"
    border_color = "#30363d" if dark_mode else "#e1e4e8"
    text_color = "#c9d1d9" if dark_mode else "#24292e"
    key_color = "#79c0ff" if dark_mode else "#0550ae"
    val_color = "#a5d6ff" if dark_mode else "#0969da"
    add_color = "#3fb950" if dark_mode else "#1a7f37"
    del_color = "#f85149" if dark_mode else "#cf222e"
    ascii_color = "#8b949e" if dark_mode else "#57606a"
    accent_gradient = "#58a6ff" if dark_mode else "#0969da"
    
    age_str = calculate_age(BIRTHDAY_STR)
    
    # Left column: ASCII Portrait
    ascii_tspans = generate_ascii_svg_tspans(
        username=username,
        x=25,
        start_y=45,
        line_height=17,
        width=40,
        dark_mode=dark_mode
    )
    
    # Right column: Developer Stats (starting x=470)
    rx = 470
    ry = 65
    
    age_line = ""
    if age_str:
        age_line = f'''
        <text x="{rx}" y="{ry}" class="key">Age / Time Lived:</text>
        <text x="{rx}" y="{ry + 22}" class="val">{age_str}</text>
        '''
        ry += 55
        
    stats_lines = f'''
    <text x="{rx}" y="{ry}" class="title">⚡ {username}'s GitHub Overview</text>
    <line x1="{rx}" y1="{ry + 10}" x2="940" y2="{ry + 10}" stroke="{border_color}" stroke-width="1"/>
    
    <text x="{rx}" y="{ry + 40}" class="key">Public Repositories:</text>
    <text x="{rx + 200}" y="{ry + 40}" class="val">{stats['repos']:,}</text>
    
    <text x="{rx}" y="{ry + 70}" class="key">Total Stars Earned:</text>
    <text x="{rx + 200}" y="{ry + 70}" class="val">⭐ {stats['stars']:,}</text>
    
    <text x="{rx}" y="{ry + 100}" class="key">Total Followers:</text>
    <text x="{rx + 200}" y="{ry + 100}" class="val">👥 {stats['followers']:,}</text>
    
    <text x="{rx}" y="{ry + 130}" class="key">Contributions (Calendar):</text>
    <text x="{rx + 200}" y="{ry + 130}" class="val">🌱 {stats['commits']:,}</text>
    '''
    
    if stats['additions'] or stats['deletions']:
        stats_lines += f'''
        <text x="{rx}" y="{ry + 160}" class="key">Lines of Code (LOC):</text>
        <text x="{rx + 200}" y="{ry + 160}">
            <tspan class="add">+{stats['additions']:,}</tspan> 
            <tspan class="del">-{stats['deletions']:,}</tspan>
        </text>
        '''

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="960px" height="510px" font-family="'JetBrains Mono', 'Fira Code', Consolas, monospace" font-size="14px">
    <style>
        .bg {{ fill: {bg_color}; stroke: {border_color}; stroke-width: 1.5px; rx: 14px; }}
        .title {{ font-size: 18px; font-weight: bold; fill: {accent_gradient}; }}
        .key {{ fill: {key_color}; font-weight: 600; }}
        .val {{ fill: {val_color}; font-weight: bold; }}
        .add {{ fill: {add_color}; font-weight: bold; }}
        .del {{ fill: {del_color}; font-weight: bold; }}
        .ascii {{ fill: {ascii_color}; font-size: 11px; white-space: pre; font-family: Consolas, 'Courier New', monospace; }}
    </style>
    
    <!-- Background Card -->
    <rect width="960px" height="510px" class="bg"/>
    
    <!-- Left Column: ASCII Portrait -->
    <text class="ascii">
{ascii_tspans}
    </text>
    
    <!-- Right Column: GitHub Statistics -->
    {age_line}
    {stats_lines}
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
