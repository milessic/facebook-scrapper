> [!WARNING]
> This is meant to use only for personal usage educational usage!
> Do not use this scrapper for scrapping sensitive data!
> Do not use this scrapper for scrapping not-public available pages!
> Do not store any data that may be protected by GDPR!

# Facebook post scrapper
Uses Browser, sqlite3

# Setup
- install ``python``
- install ``nodejs``
- instal requirements ``pip -r install requirements.txt``
- create ``urls.json`` file in root repo directory (exapmle below)
- create sqlite3 database named ``fb_scrapper.db``
```sqlite3
CREATE TABLE scraps (
    id INTEGER PRIMARY KEY,
    page_name TEXT NOT NULL,
    date TEXT NOT NULL,
    post_content TEXT NOT NULL,
    post_first_40 TEXT NOT NULL,
    notification_sent INTEGER NOT NULL,
    created_date VARCHAR(50)
);
```

# Okay, okay, but how to use it?
Scrapper supports two scenarios, without login (reccomended), and with login.

The no-login scenario is a default one, but if you pass --fullname, --email and --password, or --use-login-file (with passing path to the credentials file) it will follow login scenario.

This is a bash example:
```bash
python3 "fb.py" --fullname "FULL NAME OF YOUR ACCOUNT" --email "mail_or_login_to_login@domain.com" --password "secure password to your account" --startpath "facebook_scrapper repository directory"
python3 "notifications.py" "-i{id_of_your_run}" "-c{content type html or text}" "-d{facebook scrapper respository directory}"
```
This bash example will create a mail or text newsletter under ``notifications`` directory, you can use e.g. [pymail](https://github.com/milessic/py_mail), or any other cli mail senders to add it to the pipeline and send the notification.

# Urls example
Urls should be JSON dictionary, where key is ``display name of the page`` and value is ``url name part of the page``,
```javascript
{
"Page Full Display Name","PageFullDisplayName"
}
```
