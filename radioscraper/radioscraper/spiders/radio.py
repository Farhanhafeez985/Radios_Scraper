import scrapy
from scrapy import Request


class RadioSpider(scrapy.Spider):
    name = 'radio'
    allowed_domains = ['www.radios.com.br']
    start_urls = ['https://www.radios.com.br/lista/pais']
    custom_settings = {'ROBOTSTXT_OBEY': False, 'LOG_LEVEL': 'INFO',
                       'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
                       'RETRY_TIMES': 5,
                       'FEED_URI': 'radio.csv',
                       'FEED_FORMAT': 'csv',
                       }

    def parse(self, response):
        countries = response.xpath(
            " //div[@class='panel-body']/div[contains(@class,'item pais') and contains(a/text(),'França')]")
        for country in countries:
            country_url = country.xpath("./a/@href").get()
            yield Request(url=country_url, callback=self.parse_cities)

    def parse_cities(self, response):
        cities = response.xpath("//div[contains(@class,'item pais-cidade') and contains(a/text(),'Paris')]")
        for city in cities:
            city_url = city.xpath("./a/@href").get()
            yield Request(url=city_url, callback=self.parse_pagination)

    def parse_pagination(self, response):
        for req in self.parse_listings(response):
            yield req
        url = response.xpath("//nav[contains(@class,'pagination-body')][1]/ul/li/a[@aria-label='Próxima']/@href").get()
        if url:
            yield Request(url, self.parse_pagination)

    def parse_listings(self, response):
        radio_listing = response.xpath(
            "//div[contains(@class,'resultado')]/div//div[@class='data']/h3/a/@href").extract()
        for radio_detail_url in radio_listing:
            yield Request(url=radio_detail_url, callback=self.parse_detail)

    def parse_detail(self, response):
        genre_list = []
        genre_url_list = []

        detail_url = response.request.url
        segment_nodes = response.xpath("//p/b[contains(text(),'Segmentos:')]/following-sibling::a")

        for segment in segment_nodes:
            genre = segment.xpath('./text()').get()
            genre_url = segment.xpath('./@href').get()
            genre_list.append(genre)
            genre_url_list.append(genre_url)

        radio_name = response.xpath("//div[@id='player-infos']/div/h1/text()").get()

        city_node = response.xpath("//p/b[contains(text(),'Cidade:')]/following-sibling::a")
        city = city_node.xpath('./text()').get()
        city_url = city_node.xpath('./@href').get()

        country_node = response.xpath("//p/b[contains(text(),'País:')]/following-sibling::a")
        country = country_node.xpath('./text()').get()
        country_url = country_node.xpath('./@href').get()

        state_node = response.xpath("//p/b[contains(text(),'Estado:')]/following-sibling::a")
        if state_node:
            state = country_node.xpath('./text()').get()
            state_url = country_node.xpath('./@href').get()
        else:
            state = ''
            state_url = ''

        website = response.xpath("//p/b[contains(text(),'Site:')]/following-sibling::a/@href").get()

        item = dict()
        item['radio_name'] = radio_name
        item['genre'] = ','.join(genre_list)
        item['detail_url'] = detail_url
        item['genre_url'] = ','.join(genre_url_list)
        item['country'] = country
        item['country_url'] = country_url
        item['city'] = city
        item['city_url'] = city_url
        item['state'] = state
        item['state_url'] = state_url
        item['website'] = website

        yield item
