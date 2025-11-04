import asyncio, socket, time
import nodriver as uc
from src.utils import get_attributes
async def get_job_info(page, card):
    card_element = await card.query_selector(".job-card-job-posting-card-wrapper")  # Adjust selector as needed
    job_info = {}
    job_attributes = get_attributes(card_element)
    job_info["job_id"] = job_attributes.get("data-job-id", None)
    job_link = await card_element.query_selector("a")
    job_info["job_link"] = get_attributes(job_link).get("href", None) if job_link else None
    title_elem = await card_element.query_selector("strong")
    company = await card_element.query_selector(".artdeco-entity-lockup__subtitle")
    location = await card_element.query_selector(".artdeco-entity-lockup__caption")

    job_info["title"] = title_elem.text if title_elem else None
    job_info["company"] = company.text if company else None
    job_info["location"] = location.text if location else None

    hirer_information = await page.query_selector(".hirer-card__hirer-information")
    if hirer_information:
        hirer_profile_link = await hirer_information.query_selector("a")
        job_info["hirer_name"] = hirer_information.text if hirer_information else None
        job_info["hirer_profile_link"] = get_attributes(hirer_profile_link).get("href", None)
    else:
        job_info["hirer_name"] = None
        job_info["hirer_profile_link"] = None
    
    job_details = await page.query_selector_all(".jobs-description__container p")
    job_description = "\n".join([d.text for d in job_details]) if job_details else None
    job_info["description"] = job_description

    return job_info

def validate_job_info(job_info):
    required_fields = ["job_id", "title", "company", "location", "job_link"]
    for field in required_fields:
        if field not in job_info or not job_info[field]:
            return False
    return True