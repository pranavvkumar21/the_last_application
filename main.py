#!/usr/bin/env python3
import asyncio, socket, time
import nodriver as uc
import time
import yaml
from src.connect import connect_browser
from src.utils import make_linkedin_url, get_attributes
from src.job_data import get_job_info, validate_job_info
import json
from src.database import setup_database

CONFIG_PATH = "config/nodriver_config.yaml"
DATABASE_PATH = "database"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)



async def main():
    db = setup_database(DATABASE_PATH, include_applications=True)
    browser = await connect_browser(
        host=config["connection"]["HOST"],
        port=config["connection"]["port"],
        usr_data_dir=config["connection"]["user_data_dir"],
        headless=config["connection"]["headless"],
        no_sandbox=config["connection"]["no_sandbox"]
    )
    print("Connected to browser:", browser)

    page = await browser.get(
        make_linkedin_url(
            base_url=config["search"]["base_url"],
            keyword=config["search"]["query"],
            geo_id=config["search"]["geo_id"],
            easy_apply=config["search"]["easy_apply"]
        )
    )

    # Loop through pages. Should add this later

    await asyncio.sleep(5)  # Wait for page to load

    job_cards = await page.find_all("semantic-search-results-list__list-item")
    print(f"Found {len(job_cards)} job cards.")
    # exit()
    for job in job_cards:

        #scroll card into view so that card details load
        await job.scroll_into_view()
        await asyncio.sleep(1)
        await job.click()
        await asyncio.sleep(2)  # Wait for job details to load


        job_info = await get_job_info(page, job)
        if validate_job_info(job_info):
            await asyncio.to_thread(db.insert_job, job_info)
        else:
            print("Invalid job information:", job_info)
        # await asyncio.sleep(3)  # Pause before next job


if __name__ == "__main__":
    asyncio.run(main())