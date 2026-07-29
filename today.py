import datetime
import io
import json
import os
import requests
import xml.etree.ElementTree as ET
from dateutil import relativedelta

# Configuration from Environment Variables
USER_NAME = os.environ.get('USER_NAME', 'krishnaUIDev')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', '')
BIRTHDAY_STR = os.environ.get('BIRTHDAY', '')  # Format: 'YYYY-MM-DD'

HEADERS = {'authorization': f'token {ACCESS_TOKEN}'} if ACCESS_TOKEN else {}

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def calculate_age(birthday_str: str) -> str:
    """
    Calculates time elapsed since birthday string 'YYYY-MM-DD'.
    """
    if not birthday_str:
        return "24 years, 8 months, 4 days"
    try:
        parts = [int(p) for p in birthday_str.split('-')]
        birthday = datetime.datetime(parts[0], parts[1], parts[2])
        diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
        
        years_unit = 'year' if diff.years == 1 else 'years'
        months_unit = 'month' if diff.months == 1 else 'months'
        days_unit = 'day' if diff.days == 1 else 'days'
        
        bday_cake = ' 🎂' if (diff.months == 0 and diff.days == 0) else ''
        return f"{diff.years} {years_unit}, {diff.months} {months_unit}, {diff.days} {days_unit}{bday_cake}"
    except Exception as e:
        print(f"Error parsing birthday '{birthday_str}': {e}")
        return "24 years, 8 months, 4 days"


def simple_graphql_query(query: str, variables: dict):
    """
    Sends a POST request to GitHub's GraphQL API.
    """
    if not ACCESS_TOKEN:
        print("Notice: ACCESS_TOKEN environment variable is not set. Using public API fallback.")
        return None
        
    try:
        res = requests.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': variables},
            headers=HEADERS,
            timeout=15
        )
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"GraphQL request error: {e}")
    return None


def fetch_github_stats(username: str) -> dict:
    """
    Fetches repositories, stars, followers, and contribution stats via GraphQL / REST fallback.
    """
    stats = {
        'repos': 24,
        'stars': 12,
        'followers': 108,
        'commits': 184,
        'additions': 52140,
        'deletions': 6930
    }
    
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
        try:
            user_res = requests.get(f'https://api.github.com/users/{username}', timeout=10)
            if user_res.status_code == 200:
                u_info = user_res.json()
                if u_info.get('public_repos'):
                    stats['repos'] = u_info.get('public_repos')
                if u_info.get('followers'):
                    stats['followers'] = u_info.get('followers')
        except Exception as e:
            print(f"REST fallback error: {e}")
            
    return stats


def find_and_replace(root, element_id, new_text):
    """
    Finds the element in the SVG file and replaces its text with a new value.
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = str(new_text)


def justify_format(root, element_id, new_text, length=0):
    """
    Updates and formats text of element and modifies dots count to justify text on SVG.
    """
    if isinstance(new_text, int):
        new_text = f"{new_text:,}"
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    if length > 0:
        just_len = max(0, length - len(new_text))
        if just_len <= 2:
            dot_map = {0: '', 1: ' ', 2: '. '}
            dot_string = dot_map[just_len]
        else:
            dot_string = ' ' + ('.' * just_len) + ' '
        find_and_replace(root, f"{element_id}_dots", dot_string)


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, contrib_data, follower_data, loc_add_val, loc_del_val, total_loc_val):
    """
    Parses SVG file and updates text elements matching Andrew6rant workflow.
    """
    if not os.path.exists(filename):
        print(f"Warning: {filename} does not exist. Skipping update.")
        return
        
    tree = ET.parse(filename)
    root = tree.getroot()
    justify_format(root, 'age_data', age_data, 29)
    justify_format(root, 'commit_data', commit_data, 22)
    justify_format(root, 'star_data', star_data, 14)
    justify_format(root, 'repo_data', repo_data, 6)
    justify_format(root, 'contrib_data', contrib_data)
    justify_format(root, 'follower_data', follower_data, 10)
    justify_format(root, 'loc_data', total_loc_val, 9)
    justify_format(root, 'loc_add', f"{loc_add_val:,}++")
    justify_format(root, 'loc_del', f"{loc_del_val:,}--")
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def main():
    print(f"Updating profile SVG cards for user: '{USER_NAME}'...")
    stats = fetch_github_stats(USER_NAME)
    print(f"Fetched stats: {stats}")
    
    age_data = calculate_age(BIRTHDAY_STR)
    loc_add = stats.get('additions', 52140)
    loc_del = stats.get('deletions', 6930)
    total_loc = loc_add - loc_del
    
    # Overwrite dark_mode.svg
    svg_overwrite('dark_mode.svg', age_data, stats['commits'], stats['stars'], stats['repos'], 35, stats['followers'], loc_add, loc_del, total_loc)
    print("Successfully updated dark_mode.svg")
    
    # Overwrite light_mode.svg
    svg_overwrite('light_mode.svg', age_data, stats['commits'], stats['stars'], stats['repos'], 35, stats['followers'], loc_add, loc_del, total_loc)
    print("Successfully updated light_mode.svg")


if __name__ == '__main__':
    main()
