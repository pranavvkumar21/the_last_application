#!/usr/bin/env python3
import asyncio, socket, time
import nodriver as uc
import time
import yaml
from src.connect import connect_browser
from src.utils import make_linkedin_url, get_attributes
from src.job_data import get_job_info, validate_job_info
from src.process_application import loop_through_form
from src.the_ai_bit import VectorRetriever, get_langchain_llm
import json
from src.database import setup_database
from dotenv import load_dotenv
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description="Process job applications.")
parser.add_argument("--search_query", type=str, help="Job search query", default=None)
args = parser.parse_args()
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config" / "tla_config.yaml"
CSS_SELECTOR_PATH = ROOT_DIR / "config" / "css_selectors.yaml"
DATABASE_PATH = ROOT_DIR / "database"
DATA_PATH = ROOT_DIR / "data"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)
with open(CSS_SELECTOR_PATH, "r") as f:
    css_selectors = yaml.safe_load(f)
#get the llm
llm = get_langchain_llm()

#get default answers
with open(DATA_PATH / "default_answers.json", "r") as f:
    default_answers = json.load(f)

async def main():

    ## SETUP DATABASE AND BROWSER CONNECTION
    db = setup_database(DATABASE_PATH, include_applications=True)
    browser = await connect_browser(
        host=config["connection"]["HOST"],
        port=config["connection"]["port"],
        usr_data_dir=config["connection"]["user_data_dir"],
        headless=config["connection"]["headless"],
        no_sandbox=config["connection"]["no_sandbox"]
    )
    print("Connected to browser:", browser)
    keyword = args.search_query if args.search_query else config["search"]["query"]

    page = await browser.get(
        make_linkedin_url(
            base_url=config["search"]["base_url"],
            keyword=keyword,
            geo_id=config["search"]["geo_id"],
            easy_apply=config["search"]["easy_apply"]
        )
    )
    print("Finding jobs for query:", keyword)
    ## SETUP THE AI RETRIEVER

    the_ai = VectorRetriever(llm)
    the_ai.create_qa_chain()

    # Loop through pages. Should add this later

    await asyncio.sleep(5)  # Wait for page to load
    applied_counter = 0
    max_jobs = config["search"].get("max_jobs", 10)
    
    print(f"Found {len(job_cards)} job cards.")
    # exit()

    page_number = 1
    while applied_counter < max_jobs:
        job_cards = await page.find_all(css_selectors["job_card"]["job_card"])
        for job in job_cards:

            #scroll card into view so that card details load
            await job.scroll_into_view()
            await asyncio.sleep(1)
            title_elem = await job.query_selector(css_selectors["job_card"]["job_title"])
            await title_elem.click()
            await asyncio.sleep(2)  # Wait for job details to load


            job_info = await get_job_info(page, job)
            if validate_job_info(job_info):
                await asyncio.to_thread(db.insert_job, job_info)
            else:
                print("Invalid job information:", job_info)
            # await asyncio.sleep(3)  # Pause before next job

            #click easy apply if available
            easy_apply_btn = await page.query_selector(css_selectors["job_card"]["easy_apply_button"])
            if easy_apply_btn:
                await easy_apply_btn.scroll_into_view()
                await easy_apply_btn.click()
                print("Clicked Easy Apply button.")

                #process application
                question_answers = await loop_through_form(page, the_ai, default_answers=default_answers,use_ai=config["langchain"].get("use_ai", True))
                if question_answers is None:
                    print("Unable to process application form. Skipping to next job.")
                    continue
                result = db.save_application_qna(job_info["job_id"], question_answers)
                db.finalize_application(job_info["job_id"], result["application_id"], response_details="Easy Apply success")
                #save questions and update uploaded status in db
                applied_counter += 1
                if applied_counter >= max_jobs:
                    print(f"Reached maximum number of applications: {max_jobs}. Exiting.")
                    exit()
        page_number += 1
        #go to next page
        next_page_btn = await page.query_selector(f"button[aria-label='Page {page_number}']")
        if next_page_btn:
            await next_page_btn.scroll_into_view()
            await next_page_btn.click()
            print(f"Navigated to page {page_number}.")
            await asyncio.sleep(5)  # Wait for page to load
    


if __name__ == "__main__":
    asyncio.run(main())