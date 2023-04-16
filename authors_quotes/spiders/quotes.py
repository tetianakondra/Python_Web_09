import json

import scrapy
from itemadapter import ItemAdapter
from scrapy.item import Item, Field
from scrapy.crawler import CrawlerProcess


class QuoteItem(Item):
    tags = Field()
    author = Field()
    quote = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class MainPipline:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'fullname' in adapter.keys():
            self.authors.append(adapter.asdict())
        if 'quote' in adapter.keys():
            self.quotes.append(adapter.asdict())
        return item

    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as fd:
            json.dump(self.quotes, fd, ensure_ascii=False)
        with open('authors.json', 'w', encoding='utf-8') as fd:
            json.dump(self.authors, fd, ensure_ascii=False)


class QuoteSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["http://quotes.toscrape.com"]
    # custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "quotes.json"}
    custom_settings = {'ITEM_PIPELINES': {MainPipline: 300}}

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            author_link = quote.xpath("span/a/@href").get().strip()
            yield response.follow(
                url=self.start_urls[0] + author_link,
                callback=self.parse_author
            )
            tags = [el.strip() for el in quote.xpath(
                "div[@class='tags']/a[@class='tag']/text()").extract()]
            author = quote.xpath("span/small/text()").extract()
            quote = quote.xpath("span[@class='text']/text()").get()
            yield QuoteItem(tags=tags, author=author, quote=quote)
            next_link = response.xpath("//li[@class='next']/a/@href").get()
            if next_link:
                yield scrapy.Request(url=self.start_urls[0] + next_link)

    def parse_author(self, response):
        author_info = response.xpath("/html//div[@class='author-details']")
        fullname = author_info.xpath(
            "h3[@class='author-title']/text()").get().strip()
        born_date = author_info.xpath(
            "p/span[@class='author-born-date']/text()").get().strip()
        born_location = author_info.xpath(
            "p/span[@class='author-born-location']/text()").get().strip()
        description = author_info.xpath("div[@class='author-description']/text()").get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, description=description)


process = CrawlerProcess()
process.crawl(QuoteSpider)
process.start()
process.join()
