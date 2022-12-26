import json
import argparse
import requests
from fuzzywuzzy import fuzz


def get_paper_id_from_title(cur_title):
    res1 = search_cs_papers_es(cur_title)
    pid_hit = None
    if len(res1) > 0:
        cur_sim = fuzz.ratio(res1[0]["_source"]["title"].lower(), cur_title)
        # print("sim", cur_sim)
        if cur_sim >= 95:
            pid_hit = res1[0]["_id"]

    if pid_hit is None:
        papers = search_paper_title_via_aminer(cur_title)
        if len(papers) > 0:
            cur_sim = fuzz.ratio(papers[0]["title"].lower(), cur_title)
            # print("sim", cur_sim)
            if cur_sim >= 95:
                pid_hit = papers[0]["id"]
    return pid_hit


def search_cs_papers_es(title):
    res = requests.get("http://166.111.5.162:20222/search_cs_title_es/" + title)
    # print(res)
    res = json.loads(res.text)
    return res


def search_paper_title_via_aminer(title):
    params = [
        {"action":"searchapi.SearchPubsCommon",
         "parameters":
             {"offset":0,"size":20,"searchType":"all","switches":["lang_zh"],
              "aggregation":["year","author_year","keywords","org"],
              "query": title,
              "year_interval":1},
         "schema":{"publication":["id","year","title","title_zh","abstract","abstract_zh","authors","authors._id","authors.name","keywords","authors.name_zh","num_citation","num_viewed","num_starred","num_upvoted","is_starring","is_upvoted","is_downvoted","venue.info.name","venue.volume","venue.info.name_zh","venue.info.publisher","venue.issue","pages.start","pages.end","lang","pdf","ppt","doi","urls","flags","resources","issn","versions"]}}
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    # res = requests.get('https://api.aminer.org/api/search/pub', params=par, headers=headers)
    res = requests.post("https://apiv2.aminer.cn/n", json=params)
    res_dict = json.loads(res.text)
    papers = res_dict['data'][0]["items"]
    return papers
