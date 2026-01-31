"""
Example: Create a Custom Web Scraper Agent
"""
from agents import AgentDNA, Agent
from personality import BrainClone


def main():
    """Create a web scraper specialist"""
    
    # Load personality
    brain_clone = BrainClone()
    
    # Define specialized web scraper DNA
    scraper_dna = AgentDNA(
        role="Web Scraping Engineer",
        seniority="Senior",
        domain="E-commerce Data Extraction",
        industry_knowledge=[
            "HTML/CSS parsing",
            "Anti-bot bypass techniques",
            "Rate limiting and politeness",
            "Legal compliance (robots.txt)",
            "Data cleaning and validation"
        ],
        methodologies=[
            "BeautifulSoup/Scrapy frameworks",
            "Rotating proxies and user agents",
            "Incremental data updates",
            "Error handling and retries",
            "Structured data output"
        ],
        constraints={
            "legal": "Must respect robots.txt and terms of service",
            "rate_limit": "Max 1 request per second",
            "storage": "SQLite for local storage",
            "reliability": "Automatic retry on failures"
        },
        output_format={
            "code": "Python with type hints and docstrings",
            "data": "JSON or CSV format",
            "logs": "Structured logging with timestamps",
            "documentation": "README with usage examples"
        }
    )
    
    # Create agent
    agent = Agent(dna=scraper_dna, personality=brain_clone.get_personality())
    
    # Define task
    task = "Create a web scraper for Amazon product prices"
    context = {
        "target_url": "https://www.amazon.com/s?k=laptops",
        "data_fields": ["title", "price", "rating", "url"],
        "output_file": "products.json",
        "domain_requirements": "E-commerce scraping"
    }
    
    # Execute task
    print("🤖 Creating web scraper...")
    print(f"Agent: {agent.dna}\n")
    
    result = agent.execute_task(task, context)
    
    # Display result
    print("\n📊 Result:")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'clarification_needed':
        print("\nQuestions:")
        for question in result['questions']:
            print(question)
    else:
        print(f"\n{result.get('output', 'Task completed!')}")
    
    # Show system prompt
    print("\n" + "="*60)
    print("📝 Agent System Prompt:")
    print("="*60)
    print(agent.get_system_prompt())


if __name__ == "__main__":
    main()
