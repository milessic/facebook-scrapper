from src.sqlite3_connector import SqLite3Connector
import pathlib
import sys
from time import time
import os

help_text ="""notification creator for fb_scrapper
    -i[execution_id]    - set execution_id manually
    -c[content_type]    - content type
    -h   --help         - print help

    example:
    notifications.py -itest_1 -chtml  <- create notificaiton_test1.txt file with html formatting
"""

class NotificaitonGenerator:
    extensions = {
            "plain": "txt",
            "html": "html"
            }
    formatting = {
            "plain":{
                "hs": "=== ",
                "he": "",
                "h2s": "-- ",
                "h2e": "-- ",
                "be": "",
                "bs": "",
                "break": "------------------------------------------",
                "post_start": "",
                "post_end": "",
                "content_start": "",
                "content_end": "",
                "msg_start": "",
                "msg_end": "",
                },
            "html":{
                "msg_start": """<!doctype html><html><head><meta charset="UTF-8"></head><body style="background: #f6f4f2;font-family:'Courier New';color:#263238;">""",
                "msg_end": "</body></html>",
                "hs": """<span style="background: #FFFFFF;"><h1 style="display:block;text-align:center;margin-left:40px;margin-top: 20px;margin-right:40px;margin-bottom:10px;">""",
                "he": "</h1></span>",
                "subhs": """<span style="text-align:center;display:block;">""",
                "subhe": "</span>",
                "h2s": """<h2 style="padding-top: 10px;">""",
                "h2e": "</h2>",
                "bs": "<b>",
                "be": "</b>",
                "break": """<hr style="margin-left: 50px;margin-top: 30px;margin-bottom:20px;margin-right: 50px;">""",
                "post_start": """<div style="background: #FFFFFF;padding-left: 40px;padding-right: 40px;padding-bottom:40px;margin-left: auto;margin-right:auto;width:50%;text-align:justify;margin-bottom:40px;">""",
                "post_end": """</div>""",
                "content_start": """<span style="margin-left: 50px;margin-right:50px;margin-bottom:40px;">""",
                "content_end": """</span>""",
                }
            }

    def __init__(self, execution_id:str | None = None, starting_path:str=""):
        self.path = pathlib.Path(starting_path)
        self.db = SqLite3Connector(pathlib.Path(self.path, "fb_scrapper.db"))
        self.execution_id = execution_id if execution_id is not None else int(time())
        self.log_path = pathlib.Path(self.path, "logs", "notifications.log")
        self.notificaitons_path = pathlib.Path(self.path, "notifications")

    def fetch_all_unsent(self):
        # get all unsent
        query = (
                "SELECT page_name, date, post_content "
                "FROM scraps "
                "WHERE notification_sent=0 "
                "ORDER BY id ASC"
                )
        results = self.db.execute(query)[0]
        with open(self.log_path,"a")as f:
            for i, q in enumerate(results):
                f.write(f"==={i} Query\n{q}\n\n")
        return results
    
    def mark_all_sent(self):
        query = (
                "UPDATE scraps "
                "SET notification_sent = 1 "
                "WHERE notification_sent = 0"
                )
        self.db.execute(query)

    def prepare_notification(self, format_type:str):
        file_extension = self.extensions.get(content_type)
        file_extension = "txt" if file_extension is None else file_extension
        if format_type not in self.formatting.keys():
            raise KeyError(f"{format_type} not in {self.formatting.keys()}!")
        f = self.formatting[format_type]
        results = self.fetch_all_unsent()
        posts = {}
        for result in results:
            posts[result[0]] = []

        for result in results:
            this_post = {
                        "date": result[1],
                        "content": result[2],
                        }
            posts[result[0]].append(this_post)
        message = f"{f['msg_start']}"
        for k,v in posts.items():
            message += f"{f['hs']}{f['bs']}{k}{f['be']}{f['he']}\n{f['subhs']}{len(v)} new post{'s' if len(v) > 1 else ''}{f['subhe']}\n"
            for row in v:
                message += f['post_start'] + f['h2s'] + row["date"] + f["h2e"] + "\n"
                first_sentence_b_msg = self.bold_first_sentence(row["content"], format_type)
                message +=  f["content_start"] + first_sentence_b_msg + "\n\n\n" + f["content_end"] + f["post_end"]
            message += f['break']
        # replace \n with <br> for HTML
        if format_type == "html":
            message.replace("\n", "<br>")
        message += f["msg_end"]
        if len(message) <= (len(f["msg_end"]) + len(f["msg_start"])):
            message = self.return_template("empty", content_type)
        save_file_path = pathlib.Path(self.notificaitons_path, f"notification_{self.execution_id}.{file_extension}")
        with open(save_file_path, "w") as f:
            f.write(message)
        print(f"Saved notificaiton to {save_file_path}")
        self.mark_all_sent()

    def bold_first_sentence(self, msg:str, content_type) ->str:
        sentence_finishers = [".", "?", "!"]
        #finisher_places = {}
        # setup formatting
        f = self.formatting[content_type]
        min_sf = 1000000
        first_sf= ""
        # find first finihser
        for sf in sentence_finishers:
            #finisher_places[sf] = msg.find(sf)
            sf_place = str(msg).find(sf)
            if sf_place < 0:
                continue
            min_sf = min(min_sf, sf_place)
            if min_sf == sf_place:
                first_sf = sf
        if not first_sf:
            return msg
        msg = f['bs'] + msg.replace(first_sf, first_sf + f['be'], 1)
        # add bold end at the end if needed
        #msg = msg if f["be"] in msg else msg + f["be"]
        return msg 

    def return_template(self, template:str, content_type:str) -> str:
        f = self.formatting[content_type]
        templates = {
            "empty": f"""{f["post_start"]}{f["content_start"]}{f["msg_start"]}{f["h2s"]}There were 0 new posts from your pages{f["h2e"]}
Have a great day!{f["content_end"]}{f["post_end"]}{f["msg_end"]}"""
                }
        return templates[template]

if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(help_text)
        exit()
    exc_id = None
    content_type = "plain"
    starting_path = os.path.abspath(os.path.dirname(__file__))
    for arg in sys.argv:
        if arg.startswith("-i"):
            exc_id = arg[2:]
            continue
        if arg.startswith("-c"):
            content_type = arg[2:]
        if arg.startswith("-d"):
            starting_path = arg[2:]
    n = NotificaitonGenerator(execution_id=exc_id, starting_path=starting_path)
    n.prepare_notification(content_type)

