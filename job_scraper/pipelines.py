# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from job_scraper.db import Session, JobPost
from scrapy.exceptions import DropItem
import logging

class MySQLPipeline(object):
    def __init__(self):
        self.session = Session()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Validation
        if not adapter.get('title') or not adapter.get('job_url'):
            logging.error(f"Missing essential fields! TITLE: {adapter.get('title')}, URL: {adapter.get('job_url')}")
            raise DropItem(f"Missing essential fields: {item}")

        # Check for deduplication
        exists = self.session.query(JobPost).filter_by(job_url=adapter.get('job_url')).first()
        
        if exists:
            logging.warning(f"DUPLICATE URL DROPPED: {adapter.get('job_url')}")
            raise DropItem("Duplicate item found based on job_url.")

        # Save to DB
        new_job = JobPost(
            title=adapter.get('title'),
            company=adapter.get('company'),
            location=adapter.get('location'),
            salary=adapter.get('salary', 'Not specified'),
            job_url=adapter.get('job_url'),
            description=adapter.get('description', ''),
            source_board=adapter.get('source_board')
        )
        
        try:
            self.session.add(new_job)
            self.session.commit()
            logging.info(f"Successfully inserted: {adapter.get('title')} at {adapter.get('company')}.")
        except Exception as e:
            self.session.rollback()
            logging.error(f"Error inserting {adapter.get('title')}: {e}")
            raise DropItem("Database insertion failed.")

        return item

    def close_spider(self, spider):
        self.session.close()
