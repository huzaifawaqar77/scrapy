import scrapy
from scrapy.loader import ItemLoader
from job_scraper.items import JobScraperItem

class PythonJobsSpider(scrapy.Spider):
    name = "python_jobs"
    allowed_domains = ["python.org"]
    start_urls = ["https://www.python.org/jobs/"]

    def parse(self, response):
        self.logger.info("Parsing jobs from python.org")
        # Extract job listings
        jobs = response.xpath('//ol[contains(@class, "list-recent-jobs")]/li')
        
        for job in jobs:
            loader = ItemLoader(item=JobScraperItem(), selector=job)
            
            # Use XPath to locate exact pieces of data
            loader.add_xpath('title', './/h2/span[@class="listing-company-name"]/a/text()')
            loader.add_xpath('job_url', './/h2/span[@class="listing-company-name"]/a/@href')
            loader.add_xpath('company', './/span[@class="listing-company-name"]/text()[last()]')
            loader.add_xpath('location', './/span[@class="listing-location"]/a/text()')
            loader.add_value('source_board', 'Python.org Jobs')
            loader.add_value('salary', 'Not Disclosed') # Because python.org often doesn't show it here
            
            item = loader.load_item()
            
            # Make URL absolute
            if item.get('job_url'):
                item['job_url'] = response.urljoin(item['job_url'])
                
                # Yield request to job detail page to get description
                yield scrapy.Request(
                    url=item['job_url'],
                    callback=self.parse_job_detail,
                    meta={'item': item}
                )

        # Pagination handling
        next_page = response.xpath('//li[@class="next"]/a/@href').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_job_detail(self, response):
        item = response.meta['item']
        loader = ItemLoader(item=item, response=response)
        
        # Scrape Description details
        loader.add_xpath('description', '//div[@class="job-description"]//text()')
        
        yield loader.load_item()
