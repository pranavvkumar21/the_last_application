import asyncio, time
from src.utils import get_attributes
from pathlib import Path
import yaml
ROOT_DIR = Path(__file__).resolve().parent.parent
CSS_SELECTOR_PATH = ROOT_DIR / "config" / "css_selectors.yaml"
with open(CSS_SELECTOR_PATH, "r") as f:
    css_selectors = yaml.safe_load(f)

async def check_inline_feedback(item):
    inline_feedback = await item.query_selector(css_selectors["form_elements"]["inline_feedback"])
    if inline_feedback:
        feedback_text = inline_feedback.text
        print(" - Inline Feedback:", feedback_text)
        return feedback_text
    return None

async def loop_through_form_elements(page, the_ai, default_answers={}, use_ai=True):
    qa = {}
    form_items = await page.find_all(css_selectors["form_elements"]["form_element"])
    if not form_items:
        print("No form items found.")
        return qa
    for item in form_items:
        await item.scroll_into_view()
        label = await item.query_selector("label")
        input_elem = await item.query_selector("input, select, textarea, fieldset")
        print("Form Item:", label.text if label else "N/A")
        if input_elem.tag_name == "input":
            input_type = get_attributes(input_elem).get("type", "N/A")
            #check for inline feedback
            inline_feedback = await check_inline_feedback(item)
            print(" - Input Type:", input_type)
            if input_type in ["text"]:
                answer = await answer_questions(the_ai, label.text.strip("*"), 
                                                default_answers=default_answers, 
                                                output_options=[], 
                                                inline_feedback=inline_feedback,
                                                use_ai=use_ai)
                print(" - Answer:", answer)
                await input_elem.clear_input()
                await input_elem.send_keys(answer)
                await asyncio.sleep(1)
                
        elif input_elem.tag_name == "select":
            print(" - Select Element")
            options = await input_elem.query_selector_all("option")
            output_options = []
            for option in options:
                output_options.append(option.text)
            inline_feedback = await check_inline_feedback(item)
            answer = await answer_questions(the_ai, label.text.strip("*"), output_options=output_options, default_answers=default_answers, inline_feedback=inline_feedback)
            print(" - Answer:", answer)
            for option in options:
                if option.text.strip().lower() == answer.strip().lower():
                    await option.select_option()
                    print(f"   - Selected Option: {option.text}")
                    break
            await asyncio.sleep(1)

        elif input_elem.tag_name == "textarea":
            print(" - Textarea Element")

        elif input_elem.tag_name == "fieldset":
            print(" - Fieldset Element")
            options = await input_elem.query_selector_all("label")
            label = await input_elem.query_selector("legend")
            output_options = []
            for option in options:
                output_options.append(option.text)
            inline_feedback = await check_inline_feedback(item)
            answer = await answer_questions(the_ai, label.text.strip("*"), output_options=output_options, default_answers=default_answers, inline_feedback=inline_feedback)
            print(" - Answer:", answer)
            for option in options:
                if option.text.strip().lower() == answer.strip().lower():
                    await option.click()
                    print(f"   - Selected Option: {option.text}")
                    break
            await asyncio.sleep(1)
        qa[label.text.strip("*")] = answer
    return qa
        
async def answer_questions(the_ai, label, output_options=[],default_answers={}, inline_feedback=None, use_ai=True):
    if label in default_answers:
        answer = default_answers[label]
        print(f"Answering from default answers for '{label}': {answer}")
    else:
        if use_ai:
            if inline_feedback:
                label = f"{label}\nNote: {inline_feedback}"
            answer = the_ai.run_query(label, output_options=output_options)
        else:
            answer = default_answers.get("fallback_answer", "Prefer not to answer")
            print(f"AI disabled. Using fallback answer for '{label}': {answer}")
    return answer

async def loop_through_form(page, the_ai, default_answers={}, use_ai=True):
    count = 0
    form_counter = 0
    question_answers = {}
    while True:
        qa = await loop_through_form_elements(page, the_ai, default_answers=default_answers, use_ai=use_ai)
        #if any of qa in question_answers, break to avoid infinite loop
        if any(q in question_answers for q in qa):
            form_counter += 1
            if form_counter >=3:
                print("Detected repeated form elements. Exiting form loop.")
                dismiss_btn = await page.query_selector(css_selectors["form_elements"]["dismiss_button"])
                if dismiss_btn:
                    await dismiss_btn.click()
                    print("Clicked Dismiss button.")
                    await asyncio.sleep(1)
                    discard_btn = await page.find(css_selectors["form_elements"]["discard_button"]  )
                    if discard_btn:
                        await discard_btn.click()
                        print("Clicked Discard button.")
                return None
        question_answers = question_answers | qa
        print("Form iteration:", count)
        count += 1
        next_btn = await page.query_selector(css_selectors["form_elements"]["next_button"])
        if next_btn:
            await next_btn.click()
            print("Clicked Next button.")
            await asyncio.sleep(1)
        else:
            review_btn = await page.query_selector(css_selectors["form_elements"]["review_button"])
            if review_btn:
                await review_btn.click()
                print("Clicked Review button.")
                await asyncio.sleep(1)
            submit_btn = await page.query_selector(css_selectors["form_elements"]["submit_button"])
            if submit_btn:
                await submit_btn.click()
                print("Clicked Submit button.")
                await asyncio.sleep(4)
                dismiss_btn = await page.query_selector(css_selectors["form_elements"]["dismiss_button"])
                if dismiss_btn:
                    await dismiss_btn.click()
                    print("Clicked Dismiss button.")
                break
            print("No Next button found, assuming end of form.")
        
    return question_answers