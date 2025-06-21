import scrapy
import json
import requests
from datetime import datetime
import time
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError

class FindScheme(scrapy.Spider):
    name = "find_scheme"
    start_urls = ["https://myscheme.gov.in/"]
    allowed_domains = ["myscheme.gov.in"]
    
    # Add configuration for rate limiting
    # custom_settings = {
    #     'CONCURRENT_REQUESTS': 10,
    #     'DOWNLOAD_DELAY': 2,
    #     'RANDOMIZE_DOWNLOAD_DELAY': True,
    #     'RETRY_ENABLED': True,
    #     'RETRY_TIMES': 3,
    #     'RETRY_HTTP_CODES': [429, 500, 502, 503, 504, 408, 401, 403],
    #     'RETRY_BACKOFF_MAX': 60,
    #     'RETRY_BACKOFF_BASE': 5,
    # }

    allowed_genders = ["male", "female", "transgender"]
    allowed_castes = ["sc", "st", "obc", "general", "ews", "pvtg"]
    allowed_marital_status = ["widow", "widowed"]
    allowed_pwd = ["pwd"]

    headers = {"x-api-key": "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc"}

    def start_requests(self):
        url = "https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=%5B%5D&keyword=&sort=&from=0&size=10"
        yield scrapy.Request(
            url, 
            headers=self.headers, 
            callback=self.intermidiate_parse,
            errback=self.errback_httpbin,
            dont_filter=True
        )

    def errback_httpbin(self, failure):
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HttpError on {response.url} - {response.status}')
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error(f'DNSLookupError on {request.url}')
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error(f'TimeoutError on {request.url}')

    def intermidiate_parse(self, response):
        if response.status in [429, 403]:
            self.logger.info("Rate limited, waiting before retry...")
            time.sleep(10)  # Wait 60 seconds before retry
            yield scrapy.Request(
                response.url,
                headers=self.headers,
                callback=self.intermidiate_parse,
                dont_filter=True
            )
            return
            
        data = json.loads(response.body)
        total = data.get("data", {}).get("summary", {}).get("total", 0)
        self.logger.info(f"Total schemes found: {total}")
        
        for i in range(0, total, 10):
            url = f"https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=%5B%5D&keyword=&sort=&from={i}&size=10"
            yield scrapy.Request(
                url, 
                headers=self.headers, 
                callback=self.parse1,
                errback=self.errback_httpbin,
                dont_filter=True,
                meta={'dont_retry': False}
            )
            time.sleep(2)  # Add delay between requests

    def parse1(self, response):
        data = json.loads(response.body)
        self.logger.info(f"Processing page: {response.url}")
        self.logger.info(f"Total schemes on this page: {len(data.get('data', {}).get('hits', {}).get('items', []))}")
        
        for scheme in data.get("data", {}).get("hits", {}).get("items", []):
            slug = scheme.get("fields", {}).get("slug")
            if not slug:
                continue

            meta = {
                "name": scheme.get("fields", {}).get("schemeName"),
                "slug": slug,
                "tags": scheme.get("fields", {}).get("tags"),
                "state": scheme.get("fields", {}).get("beneficiaryState"),
                "category": scheme.get("fields", {}).get("schemeCategory"),
                "description": scheme.get("fields", {}).get("briefDescription"),
                "age": scheme.get("fields", {}).get("age")
            }
                
            yield scrapy.Request(
                url=f"https://www.myscheme.gov.in/_next/data/xwtFZuHFfQ_CBeu9-JS7Q/en/schemes/{slug}.json?slug={slug}",
                headers=self.headers,
                callback=self.get_additional_data,
                errback=self.errback_httpbin,
                meta=meta,
                dont_filter=True
            )
            time.sleep(1)  # Add delay between scheme detail requests

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




