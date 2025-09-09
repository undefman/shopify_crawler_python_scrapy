import scrapy
import json
from pathlib import Path


class ShopifySpider(scrapy.Spider):
    name = "shopify"
    start_urls = ["https://www.0stees.com/"]

    def parse(self, response):
        """Phase 1: extract collections JSON from homepage"""
        for collection in response.css("script.saswp-schema-markup-output::text").getall():
            try:
                data = json.loads(collection)

                # Save collections.json
                Path("collections.json").write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )

                # Phase 2: loop through collection links immediately
                for obj in data:
                    if "@graph" in obj:
                        for col in obj["@graph"]:
                            url = "https://www.0stees.com/collection/foo-fighters/" #col.get("url")
                            if url:
                                yield scrapy.Request(url, callback=self.parse_collection)

            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON decode failed: {e}")

    def parse_collection(self, response):
        """Extract product links from a collection"""
        for product in response.css("div.product-small a::attr(href)").getall():
            yield response.follow(product, self.parse_product, meta={"collection_url": response.url})   # 👈 pass collection URL

        # ✅ handle pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse_collection)

    def parse_product(self, response):
        """Extract product info"""
        collection_url = response.meta["collection_url"]   # 👈 retrieve it
        #yield {"collection_url": collection_url, "response": response}
        

