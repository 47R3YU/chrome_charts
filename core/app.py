""" Module containing the main classes for the app """
# standard libs
import re
import os
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
            since {datetime} -- The age of the oldest entry
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
        log.debug(f"Opening [{config.HTML_OUTPUT}] in new browser tab")
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
        self.padding = 0

    def __enter__(self):
        """ Function to establish DB connection. Called when when class is used with context manager """
        self._copy_history_db()

        log.info(f"Connecting to DB [{config.DB_PATH_LOCAL}]")
        try:
            self.dbh = sqlite3.connect(config.DB_PATH_LOCAL)
            self.cursor = self.dbh.cursor()
            self.since = self._get_history_age()
            return self
        except Exception:
            log.exception(f"Can't connect to DB at [{config.DB_PATH_LOCAL}]")
            raise

    def __exit__(self, type, value, traceback):
        """ Function to close DB connection. Called when class exits context manager """
        log.info(f"Disconnecting DB [{config.DB_PATH_LOCAL}]")
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
            else:
                # adjust the padding so long urls won't mangle the formatting when printing to console
                url_length = len(url_stripped)
                if url_length > self.padding:
                    self.padding = url_length

            stripped_urls.append(url_stripped)

        if skipped_urls:
            log.info(f"Skipped {skipped_urls} urls")

        # Use a Cunter object to count and order the list
        return list(Counter(stripped_urls).most_common(self.top))

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
        
        # Parse the result either to a HTML file or command line
        if not cli:
            Html_Handler().write_html(charts, self.since)
        else:
            print("")
            print(f"Chrome History - Top {self.top} visited URLs since {self.since}")
            print("{nr:.<3}{url:.<{padding}}{count}".format(nr="#", url="url", padding=self.padding, count="visits"))

            for i, c_url in enumerate(charts, start=1):
                print('{i:02} {url:{padding}}{count}'.format(i=i, padding=self.padding, url=c_url[0], count=c_url[1]))
            print("")

            # Log an error if jinja2 couldn't be imported so the user can fix it
            if not jinja2:
                error_msg = "HTML view is unavailable. Please execute 'pip install jinja2' and try again"
                log.error(error_msg)
                # Print to console if log printing isn't activated
                if not config.PRINT_LOG:
                    print(error_msg)
                # Cue dummy input to preven't window close
                if input("Press any key to close: "):
                    return
