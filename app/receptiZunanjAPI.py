import requests
import json


def demo_ingredient_converter(ingredients_en):
    translator_en_slo_dict = {
        # 'penne rigate': None,
        'olive oil': "Extra deviško oljčno olje nefiltrirano",
        'garlic': "ČESEN SLO ČESNEK",
        'chopped tomatoes': "BIO PARADIŽNIK DATERINO",
        # 'red chile flakes': None,
        # 'italian seasoning': None,
        'basil': "BAZILIKA NAREZANA",
        'Parmigiano-Reggiano': "BIO PARMEZAN PARMIGIANO REGGIANO",
    }
    ingredients_slo = []
    for i in ingredients_en:
        if i in translator_en_slo_dict:
            ingredients_slo.append(translator_en_slo_dict[i])
    return ingredients_slo


def search_meals(search_text):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_text}"
    response = requests.get(url)
    obj = json.loads(response.text)

    ingredients_en = [obj["meals"][0][f"strIngredient{i}"] for i in range(1, 21)]  # get all ingredients
    ingredients_en = [i for i in ingredients_en if i]  # filter out Nones, and empty strings

    ingredients_slo = demo_ingredient_converter(ingredients_en)

    return ingredients_slo

def get_stores_results_scrapy(ingredients_slo):

    scrapy_results_ingredients = []

    for ingredient in ingredients_slo:
        url = f'http://20.54.18.220/scrapy/products?title={ingredient}&fields=id%2Cstore_elem_id%2Cstore_name%2Ctitle%2Cdescription%2Ccategory%2Csales_unit%2Citem_size%2Cprice%2Curl&limit=10&offset=0'
        response = requests.get(url, headers={"accept": "application/json"})
        obj = json.loads(response.text)
        scrapy_results_ingredients.append(obj)

    return scrapy_results_ingredients


def get_results(search_text):
    #najdi sestavine na iz zunanji API
    sestavine = search_meals(search_text)

    #prevedene sestavine najdi v naši bazi
    scrapy_results = get_stores_results_scrapy(sestavine)

    return scrapy_results


# # use external api and convert english ingredients to slo -> return ingredients list
# # ['Extra deviško oljčno olje nefiltrirano', 'ČESEN SLO ČESNEK', 'BIO PARADIŽNIK DATERINO', 'BAZILIKA NAREZANA', 'BIO PARMEZAN PARMIGIANO REGGIANO']
# search_text = "Arrabiata"
# ingredients = search_meals(search_text)
# print(ingredients)

# # search our scrapy db with title (mainly spar products) -> get a list of dicts of products from our db
# scrapy_results = get_stores_results_scrapy(ingredients)
# print(scrapy_results)
# # [{'data': [{'id': '13642', 'store_elem_id': '449597', 'store_name': 'spar', 'title': 'Extra deviško oljčno olje nefiltrirano IL GREZZO, Costa D´ORO, 0,75 L', 'description': ...]
