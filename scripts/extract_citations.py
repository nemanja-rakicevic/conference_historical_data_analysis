
"""
Description:    Script for extracting the citations of the papers in the
                database. Works by sending requests to Google Scholar and
                scraping "Cited by" information.

Issues:         Google Scholar has a limit to the number of requests.
                I also tried DBLP, MS Academic and Semantic Scholar but could
                not get them to work.
"""

import os
import re
import time
import pickle
import requests


def get_num_citations(title, authors, year, timeout=100):
    time.sleep(timeout)
    request_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    }
    authors = '+'.join(['+'.join(
        [aa['given_name'], aa['family_name']]) for aa in authors])
    req_string = 'https://scholar.google.co.uk/scholar?as_q=&as_epq={title}&as_occt=title&as_sauthors={authors}&as_publication='.format(
        title=title, authors=authors)
    html_text = requests.get(req_string, headers=request_headers).text
    re_result = re.search('>Cited by (.*?)</a>', html_text)
    num_citations = None if re_result is None else int(re_result.group(1))
    return num_citations


file_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(
        file_dir, '../data/neurips_conf_data.pkl'), 'rb') as handle:
    conf_data = pickle.load(handle)


citation_lookup = {}
for kk, vv in conf_data.items():
    print("\n\nProcessing year: ", kk)
    for pi, paper_meta in enumerate(vv):
        print(" - paper [{}/{}]: {}".format(
            pi + 1, len(vv), paper_meta['title']))
        num_cit = get_num_citations(
            title=paper_meta['title'],
            authors=paper_meta['authors'],
            year=paper_meta['year'])
        citation_lookup[paper_meta['title']] = {
            'citations': num_cit
        }
        print("\t- cited by: ", num_cit)

with open(os.path.join(file_dir, '../data/citations_data.pkl'), 'wb') as handle:
    pickle.dump(citation_lookup, handle, protocol=pickle.HIGHEST_PROTOCOL)
