import scrapy
from scrapy.loader import ItemLoader
from job_scraper.items import JobScraperItem
from scrapy_playwright.page import PageMethod

class WWRemotelyPlaywrightSpider(scrapy.Spider):
    """
    This spider is specifically designed to showcase the integration of Playwright
    with Scrapy to handle Javascript-heavy websites or complex interactions.
    """
    name = "wwr_playwright"
    allowed_domains = ["weworkremotely.com"]
    start_urls = ["https://weworkremotely.com/remote-jobs/search?term=python"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    # We can execute actions on the page before yielding it.
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "li.feature"), # Wait until job rows render
                        PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    ]
                },
                callback=self.parse
            )

    async def parse(self, response):
        # We need to manually close the Playwright page if 'playwright_include_page' is True
        page = response.meta.get("playwright_page")
        if page:
            await page.close()

        self.logger.info("Playwright Page rendered and closed successfully!")
        
        jobs = response.xpath('//article/ul/li[contains(@class, "feature")]')

        for job in jobs:
            loader = ItemLoader(item=JobScraperItem(), selector=job)
            
            # Extract data
            loader.add_xpath('company', './/span[@class="company"]/text()')
            loader.add_xpath('title', './/span[@class="title"]/text()')
            loader.add_xpath('location', './/span[@class="region company"]/text()')
            # Updated XPath to specifically target the remote job postings and avoid company profiles
            loader.add_xpath('job_url', './/a[contains(@href, "/remote-jobs/")]/@href')
            loader.add_value('source_board', 'WeWorkRemotely')
            loader.add_value('salary', 'Not Disclosed') # WWR lists it only internally usually
            
            item = loader.load_item()
            
            if item.get('job_url'):
                item['job_url'] = response.urljoin(item['job_url'])
                
                self.logger.info(f"YIELDING REQUEST. Extracted title so far: {item.get('title')}")

                # We also need to use Playwright for the detail pages to bypass the 403 Forbidden errors
                yield scrapy.Request(
                    url=item['job_url'],
                    callback=self.parse_job_detail,
                    meta={
                        'item': item,
                        'playwright': True
                    }
                )

    def parse_job_detail(self, response):
        item = response.meta['item']
        loader = ItemLoader(item=item, response=response)
        
        loader.add_xpath('description', '//div[@id="job-listing-show-container"]//text()')
        
        yield loader.load_item()
