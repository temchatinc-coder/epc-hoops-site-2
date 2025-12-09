import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

# =====================================================================
# EPC TEAM STATS URLS (TEAM PAGES, NOT SCHOOL/SEASON PAGES)
# =====================================================================

TEAM_STATS_URLS: Dict[str, str] = {
    "Parkland": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/parkland-high-school-allentown-pa/stats",
    "Liberty": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/liberty-high-school-bethlehem-pa/stats",
    "William Allen": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/william-allen-high-school-allentown-pa/stats",
    "Allentown Central Catholic": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/allentown-central-catholic-high-school-allentown-pa/stats",
    "Dieruff": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/louis-e-dieruff-high-school-allentown-pa/stats",
    "Emmaus": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/emmaus-high-school-emmaus-pa/stats",
    "Whitehall": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/whitehall-high-school-whitehall-pa/stats",
    "Pocono Mountain West": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/pocono-mountain-west-high-school-pocono-summit-pa/stats",
    "Pocono Mountain East": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/pocono-mountain-east-high-school-swiftwater-pa/stats",
    "East Stroudsburg North": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/east-stroudsburg-north-high-school-dingmans-ferry-pa/stats",
    "East Stroudsburg South": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/east-stroudsburg-south-high-school-east-stroudsburg-pa/stats",
    "Pleasant Valley": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/pleasant-valley-high-school-brodheadsville-pa/stats",
    "Northampton": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/northampton-high-school-northampton-pa/stats",
    "Nazareth": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/nazareth-area-high-school-nazareth-pa/stats",
    "Bethlehem Catholic": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/bethlehem-catholic-high-school-bethlehem-pa/stats",
    "Easton": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/easton-area-high-school-easton-pa/stats",
    "Freedom": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/freedom-high-school-bethlehem-pa/stats",
    "Stroudsburg": "https://highschoolsports.lehighvalleylive.com/boysbasketball/team/stroudsburg-high-school-stroudsburg-pa/stats",
}

# Minimum games played to be included in individual leaders
MIN_GAMES = 1  # bump later if you want


# =====================================================================
# DATA CLASSES
# =====================================================================

@dataclass
class PlayerStat:
    player: str
    team: str
    gp: int
    pts: int
    two_pt: int
    three_pt: int
    fta: int
    ftm: int
    reb: int
    ast: int
    blk: int
    stl: int

    @property
    def ppg(self) -> float:
        return self.pts / self.gp if self.gp > 0 else 0.0


@dataclass
class TeamStat:
    team: str
    gp: int
    pts_for: int

    @property
    def ppg(self) -> float:
        return self.pts_for / self.gp if self.gp > 0 else 0.0


# =====================================================================
# HELPERS
# =====================================================================

def get_soup(url: str) -> BeautifulSoup:
    print(f"Fetching {url}")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def to_int(value: str) -> int:
    value = value.strip()
    if value in ("—", "-", ""):
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


# =====================================================================
# CORE PARSER – matches the layout from your screenshot
# =====================================================================

def parse_team_stats(team_name: str, stats_url: str) -> (List[PlayerStat], TeamStat):
    """
    Parses a single EPC team stats page.

    Expected column order (from your screenshot):

        Player | Grade | 2PT | 3PT | FTA | FTM | PTS | REB | AST | BLK | STL | GP

    We ignore the "Totals" row.
    """
    soup = get_soup(stats_url)

    table = soup.find("table")
    if not table:
        raise RuntimeError(f"No table found on stats page for {team_name}: {stats_url}")

    thead = table.find("thead")
    tbody = table.find("tbody")
    if not thead or not tbody:
        raise RuntimeError(f"No thead/tbody structure on stats page for {team_name}: {stats_url}")

    rows = tbody.find_all("tr")
    players: List[PlayerStat] = []

    total_team_pts = 0
    max_gp = 0

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        first_text = cells[0].get_text(strip=True)
        if first_text.lower().startswith("total"):
            # Skip totals row
            continue

        full_name_cell = cells[0].get_text(" ", strip=True)
        # Strip grade labels if present
        player_name = full_name_cell
        for grade_word in [" Senior", " Junior", " Sophomore", " Freshman"]:
            if grade_word in full_name_cell:
                player_name = full_name_cell.split(grade_word)[0]
                break

        # Column indices based on screenshot:
        # 0 = Player/Grade
        val_2pt = to_int(cells[1].get_text())
        val_3pt = to_int(cells[2].get_text())
        val_fta = to_int(cells[3].get_text())
        val_ftm = to_int(cells[4].get_text())
        val_pts = to_int(cells[5].get_text())
        val_reb = to_int(cells[6].get_text()) if len(cells) > 6 else 0
        val_ast = to_int(cells[7].get_text()) if len(cells) > 7 else 0
        val_blk = to_int(cells[8].get_text()) if len(cells) > 8 else 0
        val_stl = to_int(cells[9].get_text()) if len(cells) > 9 else 0
        val_gp = to_int(cells[10].get_text()) if len(cells) > 10 else 0

        p = PlayerStat(
            player=player_name,
            team=team_name,
            gp=val_gp,
            pts=val_pts,
            two_pt=val_2pt,
            three_pt=val_3pt,
            fta=val_fta,
            ftm=val_ftm,
            reb=val_reb,
            ast=val_ast,
            blk=val_blk,
            stl=val_stl,
        )

        players.append(p)

        total_team_pts += val_pts
        max_gp = max(max_gp, val_gp)

    team_stat = TeamStat(team=team_name, gp=max_gp, pts_for=total_team_pts)
    return players, team_stat


def build_leaders(players: List[PlayerStat], teams: List[TeamStat]) -> dict:
    eligible_players = [p for p in players if p.gp >= MIN_GAMES]
    eligible_teams = [t for t in teams if t.gp > 0]

    top_ppg = sorted(eligible_players, key=lambda p: p.ppg, reverse=True)[:15]
    top_pts = sorted(eligible_players, key=lambda p: p.pts, reverse=True)[:15]
    top_threes = sorted(eligible_players, key=lambda p: p.three_pt, reverse=True)[:15]
    top_team_ppg = sorted(eligible_teams, key=lambda t: t.ppg, reverse=True)[:10]

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "player_leaders": {
            "points_per_game": [
                {
                    "player": p.player,
                    "team": p.team,
                    "gp": p.gp,
                    "ppg": round(p.ppg, 1),
                    "pts": p.pts,
                }
                for p in top_ppg
            ],
            "points_total": [
                {
                    "player": p.player,
                    "team": p.team,
                    "gp": p.gp,
                    "pts": p.pts,
                }
                for p in top_pts
            ],
            "three_pointers_made": [
                {
                    "player": p.player,
                    "team": p.team,
                    "gp": p.gp,
                    "threes": p.three_pt,
                }
                for p in top_threes
            ],
        },
        "team_leaders": {
            "offense_points_per_game": [
                {
                    "team": t.team,
                    "gp": t.gp,
                    "ppg": round(t.ppg, 1),
                    "pts_for": t.pts_for,
                }
                for t in top_team_ppg
            ]
        },
    }


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def main():
    print("DEBUG TEAM_STATS_URLS:", TEAM_STATS_URLS)

    all_players: List[PlayerStat] = []
    all_teams: List[TeamStat] = []

    for team_name, url in TEAM_STATS_URLS.items():
        try:
            players, team_stat = parse_team_stats(team_name, url)
            all_players.extend(players)
            all_teams.append(team_stat)
            time.sleep(1.0)  # be gentle with the site
        except Exception as e:
            print(f"Error with {team_name}: {e}")

    leaders = build_leaders(all_players, all_teams)

    with open("epc_leaders.json", "w", encoding="utf-8") as f:
        json.dump(leaders, f, indent=2)

    print("Wrote epc_leaders.json")
