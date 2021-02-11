
import os
import re
import json
import pickle
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_num_citations(title, authors, year):
    ### Has issues, check
    ### Has issues, check
    authors = '+'.join(['+'.join([
        aa['given_name'], aa['family_name']]) for aa in authors])
    req_string = 'https://scholar.google.co.uk/scholar?as_q=&as_epq={title}&as_occt=title&as_sauthors={authors}&as_publication='.format(
        title=title, authors=authors)
    html_text = requests.get(req_string).text
    re_result = re.search('>Cited by (.*?)</a>', html_text)
    num_citations = None if re_result is None else int(re_result.group(1))
    return num_citations


def get_reviews(html_handle):
    reviewer_soup = BeautifulSoup(html_handle, 'html.parser')
    reviewer_dict = {}
    for reviewer in reviewer_soup.find_all('h3'):
        review_text = ''
        for sib in reviewer.find_next_siblings():
            if sib.name == "h3":
                break
            else:
                review_text += ' ' + sib.text
        re_result = re.search('Confidence in this Review (.*?)-', review_text)
        review_conf = None if re_result is None else int(re_result.group(1))
        reviewer_dict[reviewer.contents[0]] = {
            'text': review_text, 'confidence': review_conf}
    return reviewer_dict


# Check if there is already some data
if os.path.isfile('neurips_conf_data.pkl'):
    with open('neurips_conf_data.pkl', 'rb') as handle:
        conf_data = pickle.load(handle)
else:
    conf_data = {}
# Initialisation
nips_papers = 'https://papers.nips.cc/'
html_text = requests.get(nips_papers).text
soup = BeautifulSoup(html_text, 'html.parser')
# Loop through all conference years
all_conferences = [
    cc for cc in soup.find_all('li') if 'paper' in cc.a.get('href')]
all_conferences = all_conferences[::-1]
for cc in all_conferences[len(conf_data):]:
    conf_link = urljoin(nips_papers, cc.a.get('href'))
    conf_year = conf_link.split('/')[-1]
    html_text = requests.get(conf_link).text
    conf = BeautifulSoup(html_text, 'html.parser')

    # Loop through all current conference's papers
    print("\n\nProcessing: ", cc.a.contents[0])
    paper_list = []
    all_papers = [
        pp for pp in conf.find_all('li') if 'paper' in pp.a.get('href')]
    for pi, pp in enumerate(all_papers):
        # Get paper info
        print(" - paper [{}/{}]: {}".format(
            pi + 1, len(all_papers), pp.a.contents[0]))
        paper_link = urljoin(conf_link, pp.a.get('href'))
        link_file = paper_link.replace('hash', 'file')
        # Extract paper metadata
        link_meta = link_file.replace('html', 'json')
        link_meta = link_meta.replace('Abstract', 'Metadata')
        html_text = requests.get(link_meta).text
        if html_text == 'Resource Not Found':
            author_list = [
                {'given_name': aa.split(' ')[0],
                 'family_name': aa.split(' ')[1],
                 'institution': None} for aa in pp.i.contents[0].split(', ')]
            paper_meta = {
                'title': pp.a.contents[0],
                'authors': author_list,
                'abstract': None,
                'full_text': None
            }
        else:
            paper_meta = json.loads(html_text)
        # Extract paper supplemental
        link_supplement = link_file.replace('html', 'zip')
        link_supplement = link_supplement.replace('Abstract', 'Supplemental')
        html_text = requests.get(link_supplement).text
        if html_text == 'Resource Not Found':
            has_zip = False
        else:
            has_zip = True
        link_supplement = link_supplement.replace('zip', 'pdf')
        html_text = requests.get(link_supplement).text
        if html_text == 'Resource Not Found':
            has_pdf = False
        else:
            has_pdf = True
        has_supplement = has_pdf or has_zip
        # Extract paper reviews
        link_review = link_file.replace('Abstract', 'Reviews')
        html_text = requests.get(link_review).text
        if html_text == 'Resource Not Found':
            reviews = None
        else:
            reviews = get_reviews(html_text)
        # Extract scholar citation data
        num_cit = get_num_citations(
            title=paper_meta['title'],
            authors=paper_meta['authors'],
            year=conf_year)
        # Update paper info
        paper_meta.update({
            'year': conf_year,
            'citations': num_cit,
            'institutions': list(
                set([aa['institution'] for aa in paper_meta['authors']])),
            'reviews': reviews,
            'has_supplement': has_supplement})
        paper_list.append(paper_meta)
    # Update conference info
    conf_data[conf_year] = paper_list
    with open('neurips_conf_data.pkl', 'wb') as handle:
        pickle.dump(conf_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
