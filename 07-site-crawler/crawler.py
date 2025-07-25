import asyncio
import os
import pdb
import sys
from pprint import pprint
from typing import Any, Dict

from crawl4ai import (
    AdaptiveConfig,
    AdaptiveCrawler,
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig,
    LLMExtractionStrategy,
)
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    ContentRelevanceFilter,
    URLPatternFilter,
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.models import CrawlResult
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load API keys
load_dotenv()

# url = "https://www.goodwillcentraltexas.org/programs-and-services/career-opportunities-for-young-adults/"
# url = "https://excelcenterhighschool.org/ and https://excelcenterhighschool.org/contact/general-faqs/"
# url = "https://excelcenterhighschool.org/contact/general-faqs/"
# url = "https://excelcenterhighschool.org/"

# Only follow URLs containing "faq" or "docs"
url_filter = URLPatternFilter(patterns=["*faq*", "*docs*"])
# ContentRelevanceFilter: Uses similarity to a text query

browser_conf = BrowserConfig(headless=True)  # or False to see the browser

# Create a content relevance filter
relevance_filter = ContentRelevanceFilter(
    query="What is the service and who is eligible?",
    threshold=0.7,  # Minimum similarity score (0.0 to 1.0)
)

# Configure the strategy
keywords = ["eligibility", "service", "how", "who"]
crawl_strategy = BestFirstCrawlingStrategy(
    max_depth=2,
    include_external=False,
    url_scorer=KeywordRelevanceScorer(keywords=keywords, weight=0.7),
    max_pages=5,  # Maximum number of pages to crawl (optional)
    # Relevance filter greatly limits crawled pages: filter_chain=FilterChain([relevance_filter]),
)

results = []


def process_result(result: CrawlResult):
    # https://docs.crawl4ai.com/core/crawler-result/
    print(f"URL: {result.url}")
    print(f"Score: {result.metadata.get('score'), 0}")
    pprint(result.metadata)
    print("Raw Markdown length:", len(result.markdown.raw_markdown))
    # https://docs.crawl4ai.com/core/fit-markdown/
    print("Fit Markdown length:", len(result.markdown.fit_markdown))

    # pdb.set_trace()
    results.append(result)


async def async_crawl(url: str):
    md_generator = DefaultMarkdownGenerator(
        # PruningContentFilter may add around 50ms in processing time.
        # content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )

    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=crawl_strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),  # Faster alternative to default WebScrapingStrategy (which uses BeautifulSoup)
        verbose=True,
        stream=True,  # Enable streaming
        markdown_generator=md_generator,
        # cache_mode=CacheMode.BYPASS  # bypass cache to have fresh content
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        # Returns an async iterator
        async for result in await crawler.arun(url, config=config):
            # Process each result as it becomes available
            process_result(result)

        print(f"Crawled {len(results)} pages in total")


class ServiceInfo(BaseModel):
    name: str = Field(..., description="Name of the service.")
    type: str = Field(..., description="Type of the service.")
    eligibility: str = Field(..., description="Eligibility criteria for the service.")
    service_area: str = Field(..., description="Geographic area served by the service.")


async def extract_structured_data_using_llm(
    url: str,
    provider: str,
    api_token: str | None = None,
    extra_headers: Dict[str, str] | None = None,
):
    "https://docs.crawl4ai.com/extraction/llm-strategies/"
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}")
        return

    extra_llm_args: Dict[str, Any] = {
        "temperature": 0,
        "top_p": 0.9,
    }
    if extra_headers:
        extra_llm_args["extra_headers"] = extra_headers

    llm_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(provider=provider, api_token=api_token),
        schema=ServiceInfo.model_json_schema(),
        extraction_type="schema",
        instruction="Extract information about the service including its name, type, eligibility, and service area.",
        extra_args=extra_llm_args,
    )
    crawler_config = CrawlerRunConfig(
        deep_crawl_strategy=crawl_strategy,
        # Per page extraction
        extraction_strategy=llm_strategy,
        stream=True,  # Enable streaming
    )

    # TODO: prevent scraping same page (https://excelcenterhighschool.org/contact/general-faqs) more than once
    # TODO: combine several pages into one result

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        async for result in await crawler.arun(url, config=crawler_config):
            process_result(result)
            print(result.extracted_content)

    llm_strategy.show_usage()

async def adaptive_crawl(url: str):
    """
    More at https://docs.crawl4ai.com/core/adaptive-crawling/
    Sounds promising, but not yet working well.
    """

    # Caution: Can crawl external sites
    config = AdaptiveConfig(
        confidence_threshold=0.9,  # Stop when confident (default: 0.8)
        max_pages=20,  # Maximum pages to crawl (default: 50)
        # top_k_links=3,              # Links to follow per page (default: 5)
        min_gain_threshold=0.05,  # Minimum expected gain to continue (default: 0.1)
        strategy="embedding",
        # embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        n_query_variations=10,  # Number of query variations to generate
        # # Coverage parameters
        # embedding_coverage_radius=0.2,  # Distance threshold for coverage
        # embedding_k_exp=3.0,  # Exponential decay factor (higher = stricter)
        # # Stopping criteria
        # embedding_min_relative_improvement=0.1,  # Min improvement to continue
        # embedding_validation_min_score=0.3,  # Min validation score
        # embedding_min_confidence_threshold=0.03,  # Below this = irrelevant
        # # Link selection
        # embedding_overlap_threshold=0.85,  # Similarity for deduplication
        # # Display confidence mapping
        # embedding_quality_min_confidence=0.7,  # Min displayed confidence
        # embedding_quality_max_confidence=0.95  # Max displayed confidence
    )

    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler, config=config)

        # Start adaptive crawling
        result = await adaptive.digest(
            start_url=url,
            query="service name and eligibility",
        )

        # View results
        adaptive.print_stats(detailed=True)
        """Got this odd output:
            [+] Query Space (samples):
            1. are there any tips for making healthy fried rice with vegetables?
            2. how do I make vegetable fried rice from scratch?
            3. what cooking techniques are essential for perfect fried rice with vegetables?
            4. can you provide a quick recipe for vegetable fried rice?
        """
        print(f"Crawled {len(result.crawled_urls)} pages")
        print(f"Achieved {adaptive.confidence:.0%} confidence")

        pprint(result.metrics)

        pages = adaptive.get_relevant_content(top_k=5)
        for page in pages:
            print(f"\n{page['index']}: {page['url']}")
            print(f"Score: {page['score']}")
            print("Extracted Content:", page["content"][:150], "...")


async def adaptive_example():
    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler)

        # Gather information about a programming concept
        result = await adaptive.digest(
            start_url="https://realpython.com",
            query="python decorators implementation patterns",
        )

        adaptive.print_stats(detailed=True)
        print(f"Crawled {len(result.crawled_urls)} pages")
        print(f"Achieved {adaptive.confidence:.0%} confidence")
        pprint(result.metrics)

        # Get the most relevant excerpts
        for doc in adaptive.get_relevant_content(top_k=3):
            print(f"\nURL: {doc['url']}")
            print(f"Score: {doc['score']:.2%}")


# TODO: For sites with search boxes, try C4A script: https://docs.crawl4ai.com/core/c4a-script/ or https://docs.crawl4ai.com/core/page-interaction/


INSTRUCT = """structured JSON output about the described service.
The JSON output should include:
- 'name': name of the service
- 'type': what kind of service it is or the service or resource it is providing
- 'eligibility': who is eligible for the services
- 'service_area': the geographic area served by the service

If the website does not provide certain information about the service, set the corresponding field to null."""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <mode>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == "crawl":
        url = "https://excelcenterhighschool.org/contact/general-faqs/"
        asyncio.run(async_crawl(url))
    elif mode == "extract":
        url = "https://excelcenterhighschool.org/contact/general-faqs/"
        asyncio.run(
            extract_structured_data_using_llm(
                url, provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY")
            )
        )
    elif mode == "adaptive":
        url = "https://excelcenterhighschool.org/"
        asyncio.run(adaptive_crawl(url))
    elif mode == "adaptive_example":
        asyncio.run(adaptive_example())
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
