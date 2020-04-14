""" Controller to execute the app with arguments  """
# standard libs
from argparse import ArgumentParser
# app modules
from core import app, helper, config

parser = ArgumentParser()
parser.add_argument("-t", "--top",
                    dest="top",
                    type=int,
                    metavar="#",
                    default=config.DEFAULT_CHART,
                    help=f"number of entries to be displayed (default: {config.DEFAULT_CHART})")
parser.add_argument("-c", "--cli",
                    dest="cli",
                    default=False,
                    action="store_true",
                    help="parse charts to console instead of HTML")
args = parser.parse_args()

log = helper.get_logger()

log.info(f"Executing [{__file__}] with args {[(arg, getattr(args, arg)) for arg in vars(args)]}")

with app.History_Handler() as history:
    history.create_charts(top=args.top, cli=args.cli)

helper.close_logger()