import asyncio

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# url = "https://www.goodwillcentraltexas.org/programs-and-services/career-opportunities-for-young-adults/"
# url = "https://excelcenterhighschool.org/ and https://excelcenterhighschool.org/contact/general-faqs/"
url="https://excelcenterhighschool.org/contact/general-faqs/"

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=1, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url, config=config)

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
