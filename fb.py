from Browser import Browser
import traceback
import sys
import configparser
import json
from time import sleep
from random import randint
import logging 
from datetime import datetime
import pathlib
from src.sqlite3_connector import SqLite3Connector

logger = logging.getLogger(__name__)



class L:
    # Login
    accept = """(//span[contains(text(),"Zezwól na wszystkie pliki cookie") or contains(text(),"Allow all cookies")])[2]"""
    mail = """//input[@id="email"]"""
    password = """//input[@id="pass"]"""
    login_btn = """//button[@name="login"]"""

    # page
    post_div = """//*[@data-ad-preview="message"]"""
    show_more = post_div + """//div[text()="Wyświetl więcej" or text()="Show more"]"""

cp = configparser.ConfigParser()
cp.read(".config.ini")


class MyBrowser(Browser):
    fb_url = "https://facebook.com"

    def __init__(self, start_path, scrap_with_web:bool=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_path = pathlib.Path(start_path)
        self.urls= json.load(open(pathlib.Path(self.start_path, "urls.json"),"r"))
        self.console = False
        self.debug = kwargs.get("--debug")
        self.db = SqLite3Connector(database=pathlib.Path(self.start_path, "fb_scrapper.db"))
        try:
            self.headless_setting = bool(int(cp["BROWSER"]["headless"]))
        except:
            self.headless_setting = True
        try:
            self.print_name = bool(cp["FB"]["print_name"])
        except:
            self.print_name = False
        self.register_keyword_to_run_on_failure("take_screenshot")
        self.log_file_name = f"fb_log_{self.get_timestamp_file()}.log"
        self.log_file_path = pathlib.Path(self.start_path, "logs",self.log_file_name)
        self.output_file_name = f"fb_output_{self.get_timestamp_file()}.log"

    def open_fb(self):
        self.new_browser(headless=self.headless_setting)
        self.new_page(self.fb_url)
        self.wait_for_elements_state(L.accept)
        self.sleep_random(3)
        self.slow_click(L.accept)
        self.wait_for_elements_state(L.mail)
        self.sleep_random(2)
        self.save_to_log("Opened Facebook with success", console=self.console)

    def login(self, credentials:dict):
        self.slow_type_text(L.mail, credentials["email"])
        self.slow_type_text(L.password, credentials["password"])
        self.slow_click(L.login_btn)
        self.wait_for_elements_state(f"""//span[contains(text(),"{credentials['fullname']}")]""", timeout=100)
        self.save_to_log(f"Logged successfully{' as ' + credentials['fullname'] if self.print_name else ''}")

    def scrap_from_ulrs(self):
        if not len(self.urls):
            self.save_to_log("Urls were empty, no input to scrap!")
        for k,v in self.urls.items():
            try:
                self.scrap_page(k,v)
            except Exception as e:
                self.save_to_log(f"ERROR: could not scrap '{k}' due to {type(e).__name__}: {traceback.format_exc()}")

    def scrap_page(self, name, url, max_posts:int=10):
        # get last post to scrap
        # set locators
        page_name_locator = f"""//h1[text()="{name}"]"""
        # go to the page
        self.save_to_log(f"Starting scrap: '{name}'", console=self.console)
        self.go_to(url)
        self.wait_for_elements_state(page_name_locator, timeout=100, message=f"Could not verify that '{name}' was opened as '{page_name_locator}' was not found")
        # scrap data
        i = 0
        while i <= max_posts:
            print(f"\t- post number {i}")
            i += 1
            # set post locator
            this_year = datetime.now().strftime("%Y")
            previous_year = str(int(this_year) - 1)
            locator = f"({L.post_div})[{i}]"
            now_date = self.get_timestamp_post()
            date_locator = f"""//div/span[contains(text()," {this_year}") or contains(text()," ({previous_year})")]"""
            print(date_locator)
            # get post data
            # get post date
            self.hover(locator, 70, -15, force=True)
            self.sleep_random(1)
            try:
                post_date = self.get_text(date_locator)
            except Exception as e:
                self.take_screenshot(f"{self.log_file_path}""date-{index}")
                self.save_to_log(f"Could not get timestamp! {i} due to {type(e).__name__}: {e}", console=True)
                post_date = now_date
            try:
                try:
                    for e in self.get_elements(L.show_more):
                        self.slow_click(e)
                except Exception as e:
                    pass
                content = self.get_text(locator)
            except:
            # scroll to bottom if needed
                self.scroll_to_bottom()
                try:
                    content = self.get_text(locator)
                except:
                    #self.save_to_log(f"Could not get content, closing ar {i}")
                    break
            # check if post already exists
            first_40_this = self.fetch_post_by_first_40(name, content[:40])[0]
            post_exists = bool(len(first_40_this))
            try:
                #self.save_to_log("last_scrapped:\n"+str(last_scrapped[0][0]).lower()+"\n-x-x-x-\n"+ str(content[:40]).lower() + ".end", console=True)
                if post_exists:
                    # break if exsits
                    self.save_to_log(f"{name} - {i} - post already in db, breaking.", console=self.console)
                    break
            except IndexError:
                self.save_to_log(f"WARNING {name} - {i} - could not be compared with latest posts", console=self.console)
            # save 
            if self.debug:
                self.save_to_log(f"DEBUG {name} - {i} - name: {name}, date: {now_date}\n\tcontent: {content}")
            self.insert_scrapped_post(
                    page_name=name,
                    date=post_date,
                    post_content=content,
                    created_date=now_date
                    )
        self.save_to_log(f"Scrapped {i-1} posts from {name}")

    def scroll_to_bottom(self):
        self.evaluate_javascript(None, "window.scrollTo(0, document.body.scrollHeight);")
        self.sleep_random(3)

    def fetch_post_by_first_40(self, name:str, first_40:str):
        query = (
            'SELECT id '
            'FROM scraps '
            f'WHERE page_name=(?) '
            f'AND post_first_40=(?) '
            'ORDER BY id DESC '
            'LIMIT 1'
            )
        args = (name, first_40)
        return self.db.execute(query, *args)

    def insert_scrapped_post(self, page_name:str, date:str, post_content:str,created_date:str):
        query = (
                'INSERT INTO scraps '
                '(page_name, date, post_content, post_first_40, notification_sent, created_date) '
                f'VALUES ((?), (?), (?), (?), 0, (?))'
                )
        args = (page_name, date, post_content, post_content[:40], created_date)
        result = self.db.execute(query, *args)
        try:
            if "ERROR" in result[0][0]:
                self.save_to_log(f"ERROR: {page_name} - could not save post due to {result[0][0]}")
        except IndexError:
            pass
    
    def slow_click(self, selector:str, timeout:int=1):
        self.click(selector)
        self.sleep_random(timeout)

    def slow_type_text(self, selector:str, text:str, timeout:int=1):
        self.click(selector)
        self.type_text(selector, text)
        self.sleep_random(timeout)

    def sleep_random(self, base_timeout:int=1):
        r"Sleeps random time based on base_timeout +/- 100% of time"
        base_time = base_timeout * 100
        time_to_sleep = (randint(1,base_time))/100
        sleep(time_to_sleep)

    def save_to_log(self, msg, console:bool=True):
        with open(self.log_file_path, "a") as f:
            f.write(self.get_timestamp_log() + " " + str(msg) + "\n")
            print(f"wrote to {self.log_file_path}")
        if console:
            print(msg)

    def get_timestamp_post(self):
        return f"{datetime.now().strftime('%y-%m-%d %H:%M')}"

    def get_timestamp_file(self):
        return f"{datetime.now().strftime('%y_%m_%d_%H_%M')}"

    def get_timestamp_log(self):
        return f"[{datetime.now().strftime('%y-%m-%d %H:%M')}]"


if __name__ == "__main__":
    web_scrapping = True
    if "--api" in sys.argv:
        web_scrapping = False
    if "--email" in sys.argv\
    and "--password" in sys.argv\
    and "--fullname" in sys.argv\
    and "--startpath" in sys.argv:
        login_creds = {
                "email": sys.argv[sys.argv.index("--email")+1],
                "password": sys.argv[sys.argv.index("--password")+1],
                "fullname": sys.argv[sys.argv.index("--fullname")+1],
                }
        start_path = sys.argv[sys.argv.index("--startpath") + 1]
    else:
        try:
            login_creds = json.load(open("fb_creds.config.json", "r"))
            start_path = login_creds["start_path"]
        except:
            raise FileNotFoundError("Could not find 'fb_creds.config.json file or it is not JSON seriazable!'")
    b = MyBrowser(start_path = start_path)
    if web_scrapping:
        b.open_fb()
        b.login(login_creds)
        b.scrap_from_ulrs()
    else:
        b.scrap_from_endpoint("393644427360778")

