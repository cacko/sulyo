import csv
import json
import requests
from pathlib import Path


def loadall():
    countries_data = json.load(Path("countries.json").open())
    countries = {c["id"]: c for c in countries_data["countries"]}
    # https://webws.365scores.com/web/competitions/?countries=1
    keys = [f"{x}" for x in countries.keys()]
    req = requests.get(
        "https://webws.365scores.com/web/competitions/",
        params={"countries": ",".join(keys)},
    )
    p = Path("leagues.json")
    p.write_text(json.dumps(req.json()))


def makecsv():
    p = Path("leagues.json")
    json_data = json.load(p.open())
    countries = {c["id"]: c for c in json_data["countries"]}
    out = Path("leagues.csv")
    fp = out.open("w")
    writer = csv.writer(fp)
    for l in json_data["competitions"]:
        if l.get("sportId") == 1:
            country = countries[l["countryId"]].get("name")
            writer.writerow([l["id"], f'{country} - {l["name"]}'])
    fp.close()


def makejson():
    allleagues = json.load(open("leagues-all.json"))
    countries = {c.get("id"): c for c in allleagues.get("countries")}
    sports = {s.get("id"): s for s in allleagues.get("sports")}
    out = Path("leagues.json")
    out.write_text(
        json.dumps(
            [
                {
                    "id": comp.get("id"),
                    "league_id": comp.get("id"),
                    "league_name": comp.get("name"),
                    "country_id": comp.get("countryId"),
                    "country_name": countries[comp.get("countryId")].get("name"),
                    "sport_id": comp.get("sportId"),
                    "sport_name": sports[comp.get("sportId")].get("name"),
                }
                for comp in allleagues.get("competitions")
            ]
        )
    )


if __name__ == "__main__":
    makejson()
