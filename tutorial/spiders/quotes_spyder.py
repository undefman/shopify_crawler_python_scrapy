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
                            url = "https://www.0stees.com/collection/autism/" #col.get("url")
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
        collection_url = response.meta["collection_url"]

        product_id = response.css("input[name=product_id]::attr(value)").get()

        # Get all attributes
        colors = response.css("select#pa_color option::attr(value)").getall()
        sizes = response.css("select#pa_size option::attr(value)").getall()
        styles = response.css("select#pa_style option::attr(value)").getall()

        # Clean out blanks
        colors = [c for c in colors if c]
        sizes = [s for s in sizes if s]
        styles = [st for st in styles if st]

        # Loop all combinations
        for color in colors:
            for size in sizes:
                for style in styles:
                    payload = {
                        "attribute_pa_color": color,
                        "attribute_pa_size": size,
                        "attribute_pa_style": style,
                        "product_id": product_id,
                    }
                    yield scrapy.FormRequest(
                        url="https://www.0stees.com/?wc-ajax=get_variation",
                        formdata=payload,
                        callback=self.parse_variant,
                        meta={
                            "collection_url": collection_url,
                            "product_url": response.url,
                            "title": response.css("h1::text").get(),
                            "color": color,
                            "size": size,
                            "style": style,
                        },
                    )

    def parse_variant(self, response):
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.warning(f"Variant JSON parse error: {e}")
            return

        yield {
            "collection_url": response.meta["collection_url"],
            "product_url": response.meta["product_url"],
            "title": response.meta["title"],
            "color": response.meta["color"],
            "size": response.meta["size"],
            "style": response.meta["style"],
            "variant": data,  # full JSON with price, variation_id, etc.
        }

        



""" 
curl 'https://www.0stees.com/?wc-ajax=get_variation' \
  --compressed \
  -X POST \
  -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.5' \
  -H 'Accept-Encoding: gzip, deflate, br, zstd' \
  -H 'Referer: https://www.0stees.com/products/autism-nhl-vegas-golden-knights-autism-t-shirts-hoodie-tank/' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'Origin: https://www.0stees.com' \
  -H 'Connection: keep-alive' \
  -H 'Cookie: wp_woocommerce_session_9a91603cc4a03bf26f3f3af85bc28875=t_5c4ed6cd69830b0c319b4374a2e31f%7C1757562567%7C1757476167%7C%24generic%24ii0-WEKKmpFFetnrNXm2ogD0T8BJZkeNy2ZHcupV; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2025-08-25%2006%3A25%3A58%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.0stees.com%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2025-08-25%2006%3A25%3A58%7C%7C%7Cep%3Dhttps%3A%2F%2Fwww.0stees.com%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D11%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28X11%3B%20Ubuntu%3B%20Linux%20x86_64%3B%20rv%3A142.0%29%20Gecko%2F20100101%20Firefox%2F142.0; woocommerce_recently_viewed=1633343%7C1487760%7C546812%7C1367216%7C1363709%7C458047%7C464089; woocommerce_items_in_cart=1; woocommerce_cart_hash=7c661d80477e15e95709c5bee17a6c2d; PHPSESSID=5kovqnchcvv6j01eca19atttgj; sbjs_session=pgs%3D4%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fwww.0stees.com%2Fproducts%2Fautism-nhl-vegas-golden-knights-autism-t-shirts-hoodie-tank%2F' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Priority: u=0' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  --data-raw 'attribute_pa_color=black&attribute_pa_size=m&attribute_pa_style=g185-gildan-pullover-hoodie-8-oz&product_id=515579' """