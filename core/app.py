""" Module containing the main classes for the app """
# standard libs
import re
import os
import locale
import shutil
import sqlite3
import webbrowser
from datetime import datetime
from collections import Counter
# vendor libs
try:
    import jinja2
except ModuleNotFoundError:
    jinja2 = None
# app modules
from core import helper, config

# set locale to use the appropriate thousands seperator when formatting numbers
locale.setlocale(locale.LC_ALL, "")

log = helper.get_logger()


class Html_Handler():
    """ Class for handling HTML output """
    def __init__(self):
        self.env = None
        self.template = None

        if jinja2:
            self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(config.TEMPLATES_DIR))
            self.template = self.env.get_template(config.HTML_TEMPLATE)

    def write_html(self, charts, since):
        """ Render history charts as HTML from template
        
        Arguments:
            charts {list} -- List of tuples containing URL and visits, like ("www.google.de", 120)
            since {str} -- The age of the oldest entry
        """

        log.info(f"Parsing history charts to HTML -> [{config.HTML_OUTPUT}]")
        try:
            with open(config.HTML_OUTPUT, 'w') as fh:
                fh.write(self.template.render(
                    title="History Carts",
                    charts=charts,
                    top=len(charts),
                    since=since
                ))
            self._open_html_file()
        except Exception:
            log.exception("Can't create HTML file")

    def _open_html_file(self):
        """ Open the HTML file with the standard browser (new tab) """
        log.info(f"Opening [{config.HTML_OUTPUT}] in new browser tab")
        try:
            webbrowser.open(config.HTML_OUTPUT, new=2)
        except Exception:
            log.exception("Can't open HTML file in browser")


class History_Handler():
    """ Class to handle the history DB file """
    def __init__(self):
        self.dbh = None
        self.cursor = None
        self.since = None
        self.top = config.DEFAULT_CHART

    def __enter__(self):
        """ Establish DB connection. Called when when class is used with context manager """
        self._copy_history_db()

        log.debug(f"Connecting to DB [{config.DB_PATH_LOCAL}]")
        try:
            self.dbh = sqlite3.connect(config.DB_PATH_LOCAL)
            self.cursor = self.dbh.cursor()
            self.since = self._get_history_age()
            return self
        except Exception:
            log.exception(f"Can't connect to DB at [{config.DB_PATH_LOCAL}]")
            raise

    def __exit__(self, type, value, traceback):
        """ Close DB connection. Called when class exits context manager """
        log.debug(f"Disconnecting DB [{config.DB_PATH_LOCAL}]")
        self.dbh.close()

    def _copy_history_db(self):
        """ Cache the history DB locally for 1h """
        
        # Raise exception if no chrome history is found
        if not os.path.isfile(config.DB_PATH):
            log.error(f"Chrome history not found at [{config.DB_PATH}]")
            raise FileNotFoundError(f"File not found -> [{config.DB_PATH}]")
        
        # Skip file acquisition if it already exists and is not older than 1h
        if os.path.isfile(config.DB_PATH_LOCAL):
            mtime = os.path.getmtime(config.DB_PATH_LOCAL)
            log.info(f"Found [{config.DB_PATH_LOCAL}] from [{datetime.fromtimestamp(mtime)}]")
            if not mtime < datetime.now().timestamp() - 60*60: 
                return
    
        log.info(f"Copying [{config.DB_PATH}] to [{config.DB_PATH_LOCAL}]")
        try:
            shutil.copy(config.DB_PATH, config.DB_PATH_LOCAL)
        except Exception:
            log.exception(f"Can't copy [{config.DB_PATH}] to [{config.DB_PATH_LOCAL}]")
            raise

    def _query_db(self, sql_query):
        """ Helper function to execute SQL queries """
        result = self.cursor.execute(sql_query).fetchall()
        return [entry[0] for entry in result]

    def _get_history_age(self):
        """ Query the DB for the entry with the oldest age and return the timestmap """

        sql_query = f"""
        SELECT visit_time
        FROM visits
        WHERE visit_time > 0
        ORDER BY visit_time ASC
        LIMIT 1;
        """

        history_age = helper.date_from_webkit(self._query_db(sql_query)[0])
        log.info(f"Oldest history entry is from [{history_age}]")
        return history_age

    def _get_history(self):
        """ Return a DB excerpt of the chrome history """
        sql_query = f"""
        SELECT
            urls.url
        FROM
            visits
        INNER JOIN urls
            ON urls.id = visits.url
        WHERE
            urls.last_visit_time >= {helper.date_to_webkit(self.since)}
        ORDER BY
            visits.visit_time ASC;
        """

        return self._query_db(sql_query)

    def _charts_from_history(self, history):
        """ Create a charts list from the history data
        
        Arguments:
            history {list} -- DB excerpt of the chrome history
        
        Returns:
            list -- A list (of tuples) of the most visited websites like [(url, visits), ...]
        """
        regex = r"^https*:\/\/[a-z 0-9 \.\-\:]*\/"
        stripped_urls = []
        skipped_urls = 0

        log.info(f"Found [{len(history)}] entries in history")

        for url in history:
            try:
                # Do a regex search on the url. If it fails, it's not a proper web URL and is skipped
                url_stripped = re.search(regex, url, flags=re.IGNORECASE).group(0)
            except AttributeError:
                log_msg = f"Skipping {url}"

                # Shorten the urls to keep the log file tidy
                if len(url) > config.MAX_URL_LENGTH:
                    url = url[:config.MAX_URL_LENGTH]
                    log_msg = f"Skipping {url}..."

                log.debug(log_msg)
                skipped_urls += 1
                continue

            stripped_urls.append(url_stripped)

        if skipped_urls:
            log.info(f"Skipped [{skipped_urls}] urls")

        # Use a Cunter object to count and order the list
        charts = list(Counter(stripped_urls).most_common(self.top))
        # Format visits with thousands seperator before returning
        return [(url, f"{visits:n}") for url, visits in charts]


    def create_charts(self, top=None, cli=False):
        """ Main function constructing the charts by calling various internal functions and displaying the result
        
        Keyword Arguments:
            top {int} -- Number of entries to display, i.e. 50 for top 50 (default: 10)
            cli {bool} -- Whether to parse the charts to a HTML file or print it to console (default: False / HTML)
        """
        if top:
            # Update list length and check if it exceeds the limit
            self.top = top if top <= config.MAX_CHART else config.MAX_CHART
        if not jinja2:
            # Fallback to command line if jinja2 couldn't be imported
            cli = True

        # Construct the charts list 
        history = self._get_history()
        charts = self._charts_from_history(history)

        # Format date to a more internationally understandable format like '15 Jan, 2020' before parsing
        self.since = datetime.strptime(self.since, "%Y-%m-%d").strftime("%d %b, %Y")

        # Parse the result either to a HTML file or command line
        if not cli:
            Html_Handler().write_html(charts, self.since)
        else:
            # Set padding to the length of the longest url + 5; Used to keep formatting dynamic
            padding = max([len(url) for url, visits in charts]) + 5

            print("")
            print(f"Top {self.top} visited URLs since [{self.since}]")
            print("{i:.<3}{url:.<{padding}}{visits}".format(i="#", url="url", padding=padding, visits="visits"))
            
            for i, entry in enumerate(charts, start=1):
                print('{i:02} {url:{padding}}{visits}'.format(i=i, url=entry[0], padding=padding, visits=entry[1]))
            print("")

            # Log an error if jinja2 couldn't be imported so the user can fix it
            if not jinja2:
                error_msg = "HTML view is unavailable. Please execute 'pip install jinja2' and try again"
                log.error(error_msg)
                # Print to console if log printing isn't activated
                if not config.PRINT_LOG:
                    print(error_msg)
                # Cue dummy input to prevent the window closing
                if input("Press [Enter] to close "):
                    return
