# Chrome Charts

Chrome Charts is an app analyzing your browse history and presenting you a top 10 list of the most visited websites

Supported platforms as of now: **Windows**

#### Prerequisites

You'll need to have **Python 3** installed which can be aquired [here](https://www.python.org/downloads/) and **Google Chrome** where you've already accumulated a browse history

#### Installing

Either download the [app as zip](https://github.com/47R3YU/chrome_charts/archive/master.zip) and exctract it or use Git to clone it

```
git clone https://github.com/47R3YU/chrome_charts.git
```

Navigate to the app directory using the command line and install the required external modules

```
pip install -r requirements.txt
```

## Getting started
### Quick start
Simply execute [chrome_charts.py](chrome_charts.py) either by double click or via the command line
```
python chrome_charts.py
```
A HTML file containing your top 10 most visited websites will be created in the apps root directory. The HTML file will open automatically in your default browser
!["HTML output"](https://i.imgur.com/10QgRpG.png)

### Using arguments
Chrome Charts offers a few options to customize your result

| Argument      | Description                                     |
| ------------- |------------------------------------------------ |
| -h, --help    | show this help message and exit                 |
| -t #, --top # | number of entries to be displayed (default: 10) |
| -c, --cli     | parse chart to console instead of HTML         |

Those arguments are optional and can be combined freely

### Examples
Show top 50 visited URLs as HTML
```
python chrome_charts.py --top 50
```
Print top 10 (default) to the command line
```
python chrome_charts.py --cli
```
Result:
```
Chrome History - Top 10 visited URLs since 2020-01-13
#..url...........................................visits
01 https://www.youtube.com/                      8020
02 https://www.google.com/                       6424
03 https://www.reddit.com/                       2607
04 https://docs.google.com/                      1361
05 https://drive.google.com/                     425
06 https://www.dict.cc/                          242
07 https://de.wikipedia.org/                     166
08 https://stackoverflow.com/                    151
09 https://en.wikipedia.org/                     124
10 https://docs.python.org/                      112
```

## Quick documentation
### Steps of execution
* Create a copy of the chrome history in [data](/data) and cache it for 1h
* Query the history DB for all relevant entries
* Query the date of the latest entry so the user can judge the timefrime of the charts
* Filter out all non standard web URLs from the result (i.e. file:///C:/.., chrome://version etc.). Reduce all valid URLs to top level
* Count, group and order the result, creating the charts
* Parse the charts into a HTML template, save it and open it in the browser
    * If argument '--cli' was used or if the necessary modules can't be imported print result to console instead

### Config
There are a few adjustable options in the [config](/core/config.py)
| Option         | Default | Description                                                                                        |
|----------------|---------|----------------------------------------------------------------------------------------------------|
| DEFAULT_CHART  | 10      | Default length of entries shown in the charts                                                       |
| MAX_CHART      | 100     | Max. length of entries to prevent unwanted behaviour in case of abnormal user input                |
| PRINT_LOG      | False   | Send log messages additionally to stdout. Default logging writes only to file in [log](/log)       |
| LOG_LEVEL      | "INFO"  | Choose how much you want to log. Set "DEBUG" to see everything or "ERROR" for minimal logging.     |
| MAX_URL_LENGTH | 60      | Trunkate URLs if this char limit is exceeded. Used only for invalid URLs to keep the log file neat |

## Build with
* [Jinja2](https://github.com/pallets/jinja) - For HTML templating
* [Bootstrap](https://getbootstrap.com/) - For styling

## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details

## Disclaimer
Chrome Charts was mainly created to have a public showpiece on my GitHub, since all my projects thus far are private. It may seem overengineered for the little functionality it offers, but the focus of this project was rather the method of developing than the function itself.