import json
from pprint import pprint
from pathlib import Path

import requests
import pandas
import numpy as np

pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 500)
pandas.set_option('display.width', 1000)

ID = 74903118

KEY = "51F93C60271785DC50ADE931921CCC9F"
PLAYERS = {ID: 'Dave',
           138456431: 'Mall',
           135266215: 'Alea iacta est',
           176573185: 'Escuro',
           145311845: 'RetardCZE',
           221175337: 'step',
           87131513: 'Wilson',
           194747251: 'Bahno'}


def req(page, save_name=None):
    if save_name:
        path = Path.cwd() / 'res' / save_name
        if path.exists():
            with open(path, 'r') as f:
                result = json.load(f)
            return result
    response = requests.get(page)
    if response.status_code == 200:
        result = response.json()
        if save_name:
            path = Path.cwd() / 'res' / save_name
            with open(path, 'w') as f:
                json.dump(result, f)
        return result
    else:
        raise Exception

# response = requests.get(' https://api.opendota.com/api/players/74903118')
# response = requests.get(' https://api.opendota.com/api/players/74903118/matches')
# print(response)

# for player_id, name in PLAYERS.items():
#     response = req(f'https://api.opendota.com/api/players/{player_id}')
#     pprint((name, response['mmr_estimate']))
#
# exit()

heroes = req('https://api.opendota.com/api/heroes', 'heroes')
hero_dict = {}
for hero in heroes:
    hero_dict[hero['id']] = hero['localized_name']

matches = req(f'https://api.opendota.com/api/players/{ID}/matches')

# pprint(matches)
matches_count = 0
hero_table = []

for match_basic in matches:
    radiant_win = match_basic['radiant_win']
    is_radiant = None
    # pprint(match)
    try:
        match_id = match_basic['match_id']
    except KeyError:
        match_id = match_basic['result']['match_id']
    match = req(f'https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1/?match_id={match_id}&key={KEY}',
                f'matches/{match_id}')

    match_b = req(f'https://api.opendota.com/api/matches/{match_id}', f'matches/{match_id}_b')  # neither API contains all the information, use both

    match = match['result']
    #pprint(match_b)
    #exit()

    team_players = 0
    save = False
    team = {}
    for player, player_b in zip(match['players'], match_b['players']):
        #print(player['account_id'], player_b['account_id'])
        p_id = player.get('account_id')
        p_id_b = player_b.get('account_id')
        #if p_id_b:

        if p_id_b is not None and p_id in [None, 4294967295]:  # means None
            p_id = p_id_b
        elif p_id_b is None and p_id != 4294967295:
            p_id_b = p_id
        if p_id != 4294967295 and p_id_b != p_id:
            print(p_id, p_id_b)
        if p_id is None:
            continue
        if p_id in PLAYERS.keys():
            team[p_id] = {'player': PLAYERS.get(p_id, p_id), 'hero': hero_dict[player['hero_id']],
                          'gpm': player['gold_per_min'], 'xpm': player['xp_per_min'], 'kills': player['kills'],
                          'deaths': player['deaths'], 'assists': player['assists'],
                          'healing': player.get('hero_healing', np.nan), 'damage': player.get('hero_damage', np.nan),
                          'LH': player['last_hits'], 'Denies': player['denies'], 'duration': match['duration']}
            # print(PLAYERS[p_id], p_id, p_id_b, player.get('hero_healing', np.nan), player.get('hero_damage', np.nan),
            #       player_b.get('hero_healing', np.nan), player_b.get('hero_damage', np.nan))
            if p_id_b:
                for label, missing in zip(['healing', 'damage'], ['hero_healing', 'hero_damage']):
                    if np.isnan(team[p_id][label]):
                        team[p_id][label] = player_b.get(missing)
            # else:
            #     print(p_id_b, p_id, PLAYERS[p_id_b])
        if p_id == ID:
            if player['player_slot'] < 5:
                is_radiant = True
            else:
                is_radiant = False
    if (is_radiant and radiant_win) or (not is_radiant and not radiant_win):
        win = True
    else:
        win = False
    if len(team) >= 3:
        for info in team.values():
            info['win'] = win
            hero_table.append(info)
        # pprint(match['players'])
        matches_count += 1
        # print(win, team_radiant, team_dire)

df = pandas.DataFrame(hero_table)

df['kda'] = (df['kills'] + df['assists']/2) / df['deaths'].clip(1)
df['dps'] = df['damage'] / df['duration']
scale_time = 1800  # dps grows linearly up to x s
df['dps_scaled'] = np.where(df['duration'] > scale_time,  df['damage'] / (df['duration'] - scale_time / 2),
                            2 * scale_time * df['damage'] / (df['duration']*df['duration']))
df['duration'] = df['duration'] / 60

df_hero = df.groupby(['hero', 'player'])
# print(df[df['hero'] == 'Spectre'])
df_hero = df_hero.agg({'win': ['count', 'sum'], 'gpm': 'mean', 'xpm': 'mean', 'kills': 'mean',
                       'deaths': 'mean', 'assists': 'mean', 'kda': 'mean', 'healing': 'mean', 'damage': 'mean',
                       'dps': 'mean', 'dps_scaled': 'mean', 'LH': 'mean', 'Denies': 'mean', 'duration': 'mean'}).reset_index('hero')

df_hero['win_rate'] = df_hero['win']['sum'] / df_hero['win']['count']
df_hero['win_rate'] = 100 * df_hero['win_rate']
df_hero['kda_alt'] = ((df_hero['kills']['mean'] + df_hero['assists']['mean']/2) / df_hero['deaths']['mean'].clip(1))

for col in ['kills', 'deaths', 'assists']:
    df_hero[col] = df_hero[col].round(1)
for col in ['kda', 'dps', 'dps_scaled', 'win_rate', 'kda_alt']:
    df_hero[col] = df_hero[col].round(2)


df_hero[['win_rate', 'gpm', 'xpm', 'healing', 'damage', 'LH', 'Denies', 'duration']] = df_hero[['win_rate', 'gpm', 'xpm',
                                                                                    'healing', 'damage', 'LH', 'Denies',
                                                                                    'duration']].astype(int)
df_hero['count'] = df_hero['win']['count']

df_hero = df_hero[df_hero['count'] > 1]
# print(df_hero.index)
pprint(df_hero.sort_values(('kda_alt'), ascending=False)[['hero', 'count', 'win_rate', 'gpm', 'xpm', 'kills', 'deaths',
                                                            'assists', 'kda', 'kda_alt', 'healing', 'damage', 'dps', 'dps_scaled', 'LH', 'Denies',]])
