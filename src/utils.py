import urllib.parse

def get_attributes(elem):
    return {elem.attributes[i]: elem.attributes[i + 1] for i in range(0, len(elem.attributes), 2)}

def make_linkedin_url(base_url, keyword, geo_id=None, easy_apply=False):
    params = {
        "keywords": keyword,
    }
    if geo_id:
        params["geoId"] = geo_id
    if easy_apply:
        params["f_AL"] = "true"
    query = urllib.parse.urlencode(params)
    return f"{base_url}?{query}"
