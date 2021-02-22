
"""
Description:    Script for extracting the country names for the institutions
                in the database, by scraping location info from Wikipedia.
                Also finds the GDP matches from the spreadsheet.

Issues:         the Location info is not consistent on Wikipedia, or the
                institution names are not informative enough
"""

import os
import re
import pickle
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_institution_country(institution_name):
    search = "https://en.wikipedia.org/wiki/{}".format(institution_name)
    try:
        html_text = requests.get(search).text
        soup = BeautifulSoup(html_text, 'html.parser')
        if hasattr(soup.find(
                "div", attrs={'class': ['country-name']}).contents[-1], 'text'):
            return soup.find(
                "div", attrs={'class': ['country-name']}).contents[-1].text
        else:
            return str(soup.find(
                "div", attrs={'class': ['country-name']}).contents[-1])
    except:
        try:
            if hasattr(soup.find(
                    "span",
                    attrs={'class': ['country-name']}).contents[-1], 'text'):
                return soup.find(
                    "span", attrs={'class': ['country-name']}).contents[-1].text
            else:
                return str(soup.find(
                    "span", attrs={'class': ['country-name']}).contents[-1])
        except:
            try:
                if hasattr(soup.find(
                        "span",
                        attrs={'class': ['locality']}).contents[-1], 'text'):
                    return soup.find(
                        "span", attrs={'class': ['locality']}).contents[-1].text
                else:
                    return str(soup.find(
                        "span", attrs={'class': ['locality']}).contents[-1])
            except:
                try:
                    return re.search(
                        'class="country-name">(.*?)<', html_text).group(1)
                except:
                    try:
                        return re.search(
                            'class="country-name"><a href="/wiki/(.*?)"',
                            html_text).group(1)
                    except:
                        return None


file_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(file_dir, '../data/neurips_conf_data.pkl'), 'rb') as handle:
    conf_data = pickle.load(handle)


total_institutions = {}
for kk, vals in conf_data.items():
    # Unique authors and institutions
    paper_info = {}
    author_papers = {}
    institution_papers = {}
    for paper in vals:
        # Get yearly unique institutions and papers per institution
        for i_name in paper['institutions']:
            if i_name is None or i_name == '':
                continue
            if i_name in institution_papers.keys():
                institution_papers[i_name] += 1
            else:
                institution_papers[i_name] = 1
    # Update total institutions
    for t_inst in institution_papers.keys():
        if t_inst in total_institutions.keys():
            total_institutions[t_inst] += institution_papers[t_inst]
        else:
            total_institutions[t_inst] = institution_papers[t_inst]

# Sorting by number of papers
total_institutions_sorted = [
    {w: total_institutions[w]} for w in sorted(
        total_institutions,
        key=total_institutions.get,
        reverse=False) if w is not None and w != '']

print("\n\nProcessing institutions:")
country_papers = {}
for item in total_institutions_sorted:
    print(" - institution: ", list(item.keys())[0])
    country = get_institution_country(list(item.keys())[0])
    print(" ---> country: ", country)
    if country in country_papers.keys():
        country_papers[country] += list(item.values())[0]
    else:
        country_papers[country] = list(item.values())[0]
print("\nExtracted countries:\n", country_papers.keys())
with open(os.path.join(file_dir, '../data/country_papers.pkl'), 'wb') as handle:
    pickle.dump(country_papers, handle, protocol=pickle.HIGHEST_PROTOCOL)

print("\n\nProcessing GDP:")
country_gdp = {}
data = pd.read_csv(
    os.path.join(file_dir, '../data/GDP_data.csv'), encoding='utf-8')
for cc in country_papers.keys():
    if len(data.index[data.iloc[:, 0] == cc]):
        country_gdp[cc] = float(
            data.iloc[data.index[(data.iloc[:, 0] == cc)], -2])
    else:
        print("No data for", cc)
with open(os.path.join(file_dir, '../data/country_gdp.pkl'), 'wb') as handle:
    pickle.dump(country_gdp, handle, protocol=pickle.HIGHEST_PROTOCOL)
