import json
import os
from pathlib import Path

from bs4 import BeautifulSoup
import requests

from MyAnimeListPy import MyAnimeList
import MyAnimeListPy.utils
import anilist_query as al_query
from MyAnimeListPy.utils.download import download


def run():
    base_path = Path("./db/mal_files/")
    base_path.mkdir(exist_ok=True, parents=True)

    base_url = "https://myanimelist.net/anime.php?letter={}&show={}"
    search_list = ".ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    mal_client = MyAnimeList(None)
    
    for letter in search_list:
        search_results = 0

        while True:

            results_url = base_url.format(letter, search_results)

            # skip bad pages
            if not mal_client.validate_url(results_url): break

            req = download(results_url, mal_client.session, mal_client.rate_limit)    # the results page
            soup = BeautifulSoup(req.content, "html.parser")

            # Looping through each anime in the page
            for elem in soup.select("a[id^='sinfo']"):
                title = elem.select_one("strong").text
                MAL_id = MyAnimeListPy.utils.get_id(elem["href"])    # extract MAL id from url

                # Skip old entries
                if (base_path / f"{MAL_id}.json").exists():
                    print(f'Skipping "{MAL_id}" | <{title}>...')
                    continue
                else:
                    print("--------------------")

                # Get information from MAL and parse it
                print(f'Scrapping from MAL "{MAL_id}" | <{title}>...')
                MAL_metadata = mal_client.get_anime(MAL_id).gather_data()

                # Use MAL id to query AniList.co.
                print(f'Querying Anilist.co for <{title}>...')
                AL_metadata = al_query.query_idMal(MAL_id)

                # Combine MAL and AniList metadata (create function to do so).
                all_metadata = MyAnimeListPy.utils.combine_sources(MAL_metadata, AL_metadata)
                
                # print(all_metadata)
                # print(json.dumps(all_metadata))
                # print(type(all_metadata))
                # return

                try:
                    # Write the metadata to a json file, using the MAL id as the
                    # filename.
                    print(f"Dumping <{title}>...")
                    with (base_path / f"{MAL_id}.json").open("w+", encoding="utf-8") as outfile:
                        outfile.write(json.dumps(all_metadata, indent=4, ensure_ascii=False))
                except Exception as e:
                    # Ensure incomplete files are deleted.
                    print("Dumping interrupted. Deleting file.")
                    if (base_path / f"{MAL_id}.json").exists():
                        os.remove((base_path / f"{MAL_id}.json"))
                    raise e
        
            # Look for the next 50 results
            search_results += 50


if __name__ == '__main__':
    run()