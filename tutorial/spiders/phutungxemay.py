import scrapy

class PhuTungSpider(scrapy.Spider):
    name = "phutung"
    allowed_domains = ["thegioixechaydien.com.vn"]
    start_urls = ["https://thegioixechaydien.com.vn/page-1-phu-tung-xe-may-dien/"]

    def parse(self, response):
        for product in response.css("div.product"):
            name = product.css("div.product-info h6 a::text").get()
            price = product.css("div.priceInfo span.price strong::text").get()
            img = product.css("div.product-image img::attr(src)").get()

            if name:
                name = name.strip()
            if price:
                price = price.strip()

            yield {
                "name": name,
                "price": price,
                "image": img,
                "page": response.url,
            }

        # Follow pagination
        next_page = response.css("div.pnavigation p.page-nav a:last-child::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
