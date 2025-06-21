import scrapy
import json
import requests
from datetime import datetime

class FindScheme(scrapy.Spider):
    name = "find_scheme"
    start_urls = ["https://myscheme.gov.in/"]
    allowed_domains = ["myscheme.gov.in"]

    allowed_genders = ["male", "female", "transgender"]
    allowed_castes = ["sc", "st", "obc", "general", "ews", "pvtg"]
    allowed_marital_status = ["widow", "widowed"]
    allowed_pwd = ["pwd"]

    headers = {"x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"}

    def start_requests(self):
        url = "https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=%5B%5D&keyword=&sort=&from=0&size=10"
        yield scrapy.Request(
            url, headers=self.headers, callback=self.intermidiate_parse
        )

    def intermidiate_parse(self, response):
        data = json.loads(response.body)
        total = data.get("data").get("summary").get("total")
        for i in range(0, total, 10):
            url = f"https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=%5B%5D&keyword=&sort=&from={i}&size=10"
            yield scrapy.Request(url, headers=self.headers, callback=self.parse1)

    def parse1(self, response):
        data = json.loads(response.body)
        for scheme in data.get("data").get("hits").get("items"):
            slug = scheme.get("fields").get("slug")
            url = f"https://www.myscheme.gov.in/schemes/{slug}"
            name = scheme.get("fields").get("schemeName")
            tags = scheme.get("fields").get("tags")
            state = scheme.get("fields").get("beneficiaryState")
            category = scheme.get("fields").get("schemeCategory")
            description = scheme.get("fields").get("briefDescription")
            age = scheme.get("fields").get("age")

            if not slug:
                continue
                
            yield scrapy.Request(
                url=f"https://www.myscheme.gov.in/_next/data/xwtFZuHFfQ_CBeu9-JS7Q/en/schemes/{slug}.json?slug={slug}",
                headers=self.headers,
                callback=self.get_additional_data,
                meta={"name": name, "slug": slug, "tags": tags, "state": state, "category": category, "description": description, "age": age}
            )

    def get_additional_data(self, response):
        data = json.loads(response.body)
        name = response.meta["name"]
        slug = response.meta["slug"]
        tags = response.meta["tags"]
        state = response.meta["state"]
        category = response.meta["category"]
        description = response.meta["description"]
        age = response.meta["age"]

        try:
            benefits_md = data["pageProps"]["schemeData"]["en"]["schemeContent"][
                "benefits_md"
            ]
        except Exception as e:
            benefits_md = None
            print(f"Error extracting benefits: {e}")

        try:
            exclusions_md = data["pageProps"]["schemeData"]["en"]["schemeContent"][
                "exclusions_md"
            ]
        except Exception as e:
            exclusions_md = None
            print(f"Error extracting exclusions: {e}")

        try:
            process_md = data["pageProps"]["schemeData"]["en"]["applicationProcess"][0][
                "process_md"
            ]
        except Exception as e:
            process_md = None
            print(f"Error extracting application process: {e}")

        try:
            eligibilityDescription_md = data["pageProps"]["schemeData"]["en"][
                "eligibilityCriteria"
            ]["eligibilityDescription_md"]
        except Exception as e:
            eligibilityDescription_md = None
            print(f"Error extracting eligibility description: {e}")

        try:
            documentsRequired_md = data["pageProps"]["docs"]["data"]["en"][
                "documentsRequired_md"
            ]
        except Exception as e:
            documentsRequired_md = None
            print(f"Error extracting documents required: {e}")

        yield {
            "name": name,
            "slug": slug,
            "url": f"https://www.myscheme.gov.in/schemes/{slug}",
            "tags": tags,
            "state": state,
            "category": category,
            "description": description,
            "age": age,
            "benefits": benefits_md,
            "exclusions": exclusions_md,
            "process": process_md,
            "eligibility": eligibilityDescription_md,
            "documents_required": documentsRequired_md,
        }
