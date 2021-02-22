
"""
Description:    Script for extracting the total world population by year.

"""

import os
import pickle
import requests
from bs4 import BeautifulSoup


search = "https://www.worldometers.info/world-population/world-population-by-year/"
html_text = requests.get(search).text
soup = BeautifulSoup(html_text, 'html.parser')

world_population = {}
for ss in soup.find_all("tr"):
    if hasattr(ss.contents[1], "text") and (ss.contents[1].text).isdigit():
        year = int(ss.contents[1].text)
        pop_global = int(ss.contents[3].text.replace(',', ''))
        pop_urban = int(ss.contents[-4].text.replace(',', '')) \
            if ss.contents[-4].text.replace(',', '').isdigit() else None
        world_population[year] = {
            'pop_global': pop_global,
            'pop_urban': pop_urban}
        print("--- {}: {}".format(year, world_population[year]))

file_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(
        file_dir, '../data/world_population.pkl'), 'wb') as handle:
    pickle.dump(world_population, handle, protocol=pickle.HIGHEST_PROTOCOL)
