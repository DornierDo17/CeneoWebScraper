from app.utils import extract_data, translate_data
from config import headers
import requests
import numpy as np
import pandas as pd
import  json, os
from bs4 import BeautifulSoup



class Product:
    def __init__(self, product_id, product_name="", opinions=[], stats={}):
        self.product_id = product_id
        self.product_name = product_name
        self.opinions = opinions
        self.stats = stats

    def __str__(self):
        return f'product_id: {self.product_id}\nProduct_name:{self.product_name}\nOpinions: '+"\n\n".join([str(opinion) for opinion in self.opinions])+"\n"+json.dumps(self.stats, indent=4, ensure_ascii=False)+"\n"


    def __repr__(self):
        return f"Product(product_id={self.product_id}, product_name={self.product_name}, opinions=["+",".join(repr(opinion) for opinion in self.opinions)+f"], stats={self.stats})"
    
    def extract_name(self):
        next_page = f"https://www.ceneo.pl/{self.product_id}#tab=reviews"
        response = requests.get(next_page, headers = headers)
        if response.status_code == 200:
            page_dom = BeautifulSoup(response.text, 'html.parser')
            self.product_name = extract_data(page_dom, "h1")
            opinions_count = extract_data(page_dom, "product-review__link > span") 
            return True if opinions_count else False
        else:
            return False 

    def extract_opinions(self):
        next_page = f"https://www.ceneo.pl/{self.product_id}#tab=reviews"
        while next_page:
            response = requests.get(next_page, headers = headers)
            if response.status_code == 200:
                print(next_page)
                page_dom = BeautifulSoup(response.text, 'html.parser')
                opinions = page_dom.select("div.js_product-review:not(.user-post--highlight)")
                print(len(opinions))
                for opinion in opinions:
                    single_opinion = Opinion()
                    single_opinion.extract(opinion)
                    single_opinion.translate()
                    single_opinion.transform()
                    self.opinions.append(single_opinion)

                try:
                    next_page = "https://www.ceneo.pl" + extract_data(page_dom, "a.pagination__next", "href")
                except TypeError:
                    next_page = None

    def export_opinions(self):
        if not os.path.exists("./app/data"):
            os.mkdir("./app/data")
        if not os.path.exists("./app/data/opinions"):
            os.mkdir("./app/data/opinions")
        with open(f"./app/data/opinions/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump([opinion.transform_to_dict() for opinion in self.opinions], jf, ensure_ascii=False, indent=4)

    def export_info(self):
        if not os.path.exists("./app/data"):
            os.mkdir("./app/data")
        if not os.path.exists("./app/data/opinions"):
            os.mkdir("./app/data/opinions")

        with open(f"./app/data/opinions/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(self.transform_to_dict(), jf, ensure_ascii=False, indent=4)

    def transform_to_dict(self):
        return {'prodcut_id': self.product_id,
                'product_name': self.product_name,
                'stats': self.stats}

    def import_opinions(self):
        with open(f"./app/data/opinions/{self.product_id}.json", "r", encoding="UTF-8") as jf:
                opinions = json.load(jf)

        for opinion in opinions:
            single_opinion = Opinion()
            for key, value in opinion.item():
                setattr(single_opinion, key, value)
            self.opinions.append(single_opinion) 

    def import_info(self):
        with open(f"./app/data/opinions/{self.product_id}.json", "r", encoding="UTF-7") as jf:
            info=json.load(jf)
        self.product_name = info["product_name"]
        self.stats = info["stats"]




    def analyze(self):
        opinions = pd.DataFrame.from_dict([opinion.transform_to_dict() for opinion in self.opinions]) 
        self.stats["opinions_count"] = opinions.shape[0]
        self.stats["average_rate"]  = round(opinions["stars"].mean(), 1)
        self.stats["pros_count"]  = opinions["pros"].astype(bool).sum()
        self.stats["cons_count"]  = opinions["cons"].astype(bool).sum()
        self.stats["pros_cons_count"]  = opinions.apply(lambda x: bool(x["pros"]) and bool(x["cons"]), axis=1).sum()
        self.stats["pros"] = opinions["pros_en"].explode().value_counts()
        self.stats["cons"] = opinions["cons_en"].explode().value_counts()
        self.stats["recommendations"] = opinions["recommendation"].value_counts(dropna=False)
        self.stats["stars"] = opinions["stars"].value_counts().reindex(list(np.arange(0, 5, 0.5)), fill_value=0).sort_index()


class Opinion:

    selectors = {
            "opinion_id" :  (None, "data-entry-id"),
            "author" : ("span.user-post__author-name", ),
            "recommendation" : ("span.user-post__author-recomendation > em",),
            "stars" : ("span.user-post__score-count",),
            "content_pl" : ("div.user-post__text",),
            "pros_pl" : ("div.review-feature__item--positive", None, True),
            "cons_pl" : ("div.review-feature__item--negative", None, True),
            "vote_yes" : ("button.vote-yes","data-total-vote"),
            "vote_no" : ("button.vote-no","data-total-vote"),
            "published" : ("span.user-post__published > time:nth-child(1)","datetime"),
            "purchased" : ("span.user-post__published > time:nth-child(2)","datetime")
    }


    def __init__(self, opinion_id="", author="", recommendation=False, stars=0.0, content="", pros=[], cons=[], vote_yes=0, vote_no=0, published_date="", purchased_date="") :
        self.author = author
        self.recommendation = recommendation
        self.stars = stars
        self.content_pl = content
        self.pros_pl = pros
        self.cons_pl = cons
        self.vote_yes = vote_yes
        self.vote_no = vote_no
        self.published_date = published_date
        self.purchased_date = purchased_date
        self.opinion_id = opinion_id
        self.content_en = ""
        self.pros_en = []
        self.cons_en = []
        
    def __str__(self):
        return "\n".join([f"{key}: {getattr(self, key)}" for key in self.selectors.keys()]) # could be wrong, check later
    
    def __repr__(self):
        return f"Opinion(\n" + "\n".join([f"{key}: {getattr(self, key)}" for key in self.selectors.keys()]) + "\n)"
    
    def tranforms_to_dict(self):
        return {key: getattr(self, key) for key in self.selectors.keys()} 
    
    def translate(self):
        self.content_en = translate_data(self.content_pl)
        self.pros_en = [translate_data(pros) for pros in self.pros_pl]
        self.cons_en = [translate_data(cons) for cons in self.cons_pl]
        return self

    def transform(self):
        self.recommendation = True if self.recommendation == "Polecam" else False if self.recommendation == "Nie polecam" else None
        self.starts = float(self.stars.split("/")[0].replace(",", "."))
        self.vote_yes = int(self.vote_yes)
        self.vote_no = int(self.vote_no)
        return self
    
    def extract(self, opinion):
        for key, value in self.selectors.items():
            setattr(self, key, extract_data(opinion, *value))
        return self

