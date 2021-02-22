
"""
Description:    Main script for downloading the paper information from the
                conference website.
                Also tries to extract the citations (see extract_citations.py)

"""

import os
import re
import json
import pickle
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_num_citations(title, authors, year):
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

offset_conf = len(conf_data)
for cc in all_conferences[offset_conf:]:
    conf_link = urljoin(nips_papers, cc.a.get('href'))
    conf_year = conf_link.split('/')[-1]
    html_text = requests.get(conf_link).text
    conf = BeautifulSoup(html_text, 'html.parser')

    # Loop through all current conference's papers
    print("\n\nProcessing: ", cc.a.contents[0])
    paper_list = []
    offset_papers = len(paper_list)
    all_papers = [
        pp for pp in conf.find_all('li') if 'paper' in pp.a.get('href')]

    for pi, pp in enumerate(all_papers[offset_papers:]):

        # Get paper info
        print(" - paper [{}/{}]: {}".format(
            pi + 1 + offset_papers, len(all_papers), pp.a.contents[0]))
        paper_link = urljoin(conf_link, pp.a.get('href'))
        html_paper = requests.get(paper_link).text

        # Extract paper metadata
        if "Metadata" in html_paper:
            link_file = paper_link.replace('hash', 'file')
            link_meta = link_file.replace('html', 'json')
            link_meta = link_meta.replace('Abstract', 'Metadata')
            html_text = requests.get(link_meta).text
            if html_text == 'Resource Not Found':
                conf = BeautifulSoup(html_paper, 'html.parser')
                abstract_text = conf.find(
                    'h4',
                    string='Abstract').next_sibling.next_sibling.contents[0]
                abstract = None if abstract_text == 'Abstract Unavailable' \
                    else abstract_text
                abstract = abstract.replace('<p>', '')
                abstract = abstract.replace('</p>', '')
                abstract = abstract.replace('\n', ' ')
                author_list = [
                    {'given_name': aa.split(' ')[0],
                     'family_name': aa.split(' ')[1],
                     'institution': None}
                    for aa in pp.i.contents[0].split(', ')]
                paper_meta = {
                    'title': str(pp.a.contents[0]),
                    'authors': author_list,
                    'abstract': abstract,
                    'full_text': None}
            else:
                paper_meta = json.loads(html_text)
                if 'full_text' in paper_meta.keys():
                    paper_meta['full_text'] = paper_meta['full_text'].replace(
                        '\n', ' ')
        else:
            # make nicer not copy
            conf = BeautifulSoup(html_paper, 'html.parser')
            abstract_text = conf.find(
                'h4',
                string='Abstract').next_sibling.next_sibling.contents[0]
            abstract = None if abstract_text == 'Abstract Unavailable' \
                else str(abstract_text)
            abstract = abstract.replace('<p>', '')
            abstract = abstract.replace('</p>', '')
            abstract = abstract.replace('\n', ' ')
            author_list = [
                {'given_name': aa.split(' ')[0],
                 'family_name': aa.split(' ')[1],
                 'institution': None} for aa in pp.i.contents[0].split(', ')]
            paper_meta = {
                'title': str(pp.a.contents[0]),
                'authors': author_list,
                'abstract': abstract,
                'full_text': None}

        # Extract paper supplemental
        if "Supplemental" in html_paper:
            has_supplement = True
        else:
            has_supplement = False

        # Extract paper reviews
        if "Reviews" in html_paper:
            link_file = paper_link.replace('hash', 'file')
            link_review = link_file.replace('Abstract', 'Reviews')
            html_text = requests.get(link_review).text
            reviews = get_reviews(html_text)
        else:
            reviews = None

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

    # Update conference info and save to file
    conf_data[conf_year] = paper_list
    with open('../data/neurips_conf_data.dat', 'wb') as handle:
        pickle.dump(conf_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # prevents losing data
    os.system("mv ../data/neurips_conf_data.dat ../data/neurips_conf_data.pkl")
