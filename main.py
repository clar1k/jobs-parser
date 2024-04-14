from typing import List
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pydantic import BaseModel
import requests
from mongo_connection import get_mongo_client
import time
from gemini import Gemini

WORK_UA_URL = "https://www.work.ua"


class WorkUaJobPost(BaseModel):
    company: str
    title: str
    place: str
    salary: str
    description: str
    is_verified: bool


def parse_single_work_ua_page(page_number: int = 1):
    user_agent = UserAgent()
    job_link_response = requests.get(
        f"{WORK_UA_URL}/jobs/?ss=1&page={page_number}",
        headers={"User-Agent": user_agent.random},
    )
    html = job_link_response.content
    card_css_class = "card"
    soup = BeautifulSoup(html, "html.parser")

    active_jobs = soup.find_all(
        "div",
        attrs={"class": card_css_class},
    )
    jobs_parsed: List[WorkUaJobPost] = []

    for job_soup in active_jobs:
        try:
            title_container = job_soup.find("h2")
            title = title_container.text
            job_link = title_container.find("a").get("href")

            job_link_response = requests.get(
                WORK_UA_URL + job_link, headers={"User-Agent": user_agent.random}
            )

            job_link_html = job_link_response.content
            job_link_soup = BeautifulSoup(job_link_html, "html.parser")
            description = job_link_soup.find("div", attrs={"id": "job-description"})
            description = description.text
            salary, company = job_soup.find_all("span", attrs={"class": "strong-600"})
            salary = salary.text
            company = company.text

            print(job_link)
            place = (
                job_soup.find("div", attrs={"class": "add-top-xs"}).find("span").text
            )

            work_ua_job_post = WorkUaJobPost(
                company=company.replace("\n", ""),
                title=title.replace("\n", ""),
                place=place.replace("\n", ""),
                salary=salary.replace("\n", ""),
                description=description.replace("\n", ""),
                is_verified=False,
            )

            jobs_parsed.append(work_ua_job_post)
        except Exception as error:
            print(error)
            continue
    return jobs_parsed


def main():
    client = get_mongo_client()
    db = client["helphub"]

    averall_parsed = []
    for page_number in range(0, 2):
        print(f"Processing page {page_number}...")
        job_posts = parse_single_work_ua_page(page_number)
        averall_parsed.extend(job_posts)
        time.sleep(5)
    print("Started inserting to db")
    for parsed_job in averall_parsed:
        db["parsed_jobs"].insert_one(dict(parsed_job))
        time.sleep(5)


COOKIES = {
    "SEARCH_SAMESITE": "CgQIrpoB",
    "SID": "g.a000hwhc-52CldPiEewFuIeSfSPedevPUh0wrPQQm5gejTKzOvlxzu9ZvfCc2qqlvHfhsHLOTwACgYKAUsSAQASFQHGX2MiHifQ5czfOCf3LfpA0N1TOhoVAUF8yKo8D0yGUF6J2J_3k9teUfv90076",
    "__Secure-1PSID": "g.a000hwhc-52CldPiEewFuIeSfSPedevPUh0wrPQQm5gejTKzOvlxNDdrkX-kg9SbTbpO4UHXBgACgYKATgSAQASFQHGX2MiDYxNZPRRmuSCK7UzwB9IrhoVAUF8yKq1911ZW03bUf1lFwGDtwVP0076",
    "__Secure-3PSID": "g.a000hwhc-52CldPiEewFuIeSfSPedevPUh0wrPQQm5gejTKzOvlxo3s7aCeqmOCfJJi2Yej8qQACgYKAU4SAQASFQHGX2MiQnMjvClT4CFr4uIknaYughoVAUF8yKocxFAphkYwa2gEu1YY9yIU0076",
    "HSID": "AEVWxQmRXC3-XT_3H",
    "SSID": "AZGL30Pts6bxCfPJM",
    "APISID": "re8R3EjPI_7EgWUC/Am6wns0u6neuFWs-N",
    "SAPISID": "qgu2nHHc0UOIh4gv/A0G2xuMOgpG4q0Ht5",
    "__Secure-1PAPISID": "qgu2nHHc0UOIh4gv/A0G2xuMOgpG4q0Ht5",
    "__Secure-3PAPISID": "qgu2nHHc0UOIh4gv/A0G2xuMOgpG4q0Ht5",
    "NID": "512",
    "AEC": "AQTF6Hw4iQyftScibUkpj0TkuNSeWyozyK3DsSUMCZuPmvIzxY0Y9VZ5JQ",
    "1P_JAR": "2024-04-14-06",
    "__Secure-ENID": "18.SE",
    "__Secure-1PSIDTS": "sidts-CjIB7F1E_G3Bl2SFBXBvF2ijDiZUJK1UouBIIAyyMY2tU8L7OHvmL5EpCx79vBSSO9ld6RAA",
    "__Secure-3PSIDTS": "sidts-CjIB7F1E_G3Bl2SFBXBvF2ijDiZUJK1UouBIIAyyMY2tU8L7OHvmL5EpCx79vBSSO9ld6RAA",
    "SIDCC": "AKEyXzWEwywJ1hWhgbfT71kl_8Q6XZOTE65A1zvDWo-gDM-PoyGlXv_VQ6Rj7GJnfLb3e5BbYLdc",
    "__Secure-1PSIDCC": "AKEyXzVoXoWwPN1R-nr2qgHvlj043VSTLnZUNHdpmPzDcxqYYs1g6W52HRrMmz-P7SbnQ3If8ZXF",
    "__Secure-3PSIDCC": "AKEyXzVEv_mnhEjiHq_hwPsKUwz8yK1rpxTZOWjFpDERhLWzeSb5aot3Ns8xSUmHC0ls9z0bDBk",
}


def filter_with_gemini_api():
    GeminiClient = Gemini(cookies=COOKIES)
    db = get_mongo_client()
    parsed_jobs = db["helphub"]["parsed_jobs"].find()
    parsed_jobs = map(lambda job: dict(job), list(parsed_jobs))
    parsed_jobs = list(parsed_jobs)

    for job in parsed_jobs:
        response = GeminiClient.generate_content(
            f"""
            Привіт. 
            Я тобі зараз відправлю вакансії з Work.ua, і ти маєш визначити, 
            чи інваліди зможуть бути здатні працювати на цих вакансіях. 
            Твоя відповідь має бути тільки - якщо так ( людина може працювати ), то відправ мені 'true', якщо ні - 'false'. 
            Якщо ти не впевнений, то відправ мені 'false'. Оріентуйся на III група інвалідності
            {job}
        """
        )
        if response.payload == "true":
            job["is_verified"] = True
            db["helphub"]["verified_jobs"].insert_one(job)
        else:
            pass


if __name__ == "__main__":
    filter_with_gemini_api()
