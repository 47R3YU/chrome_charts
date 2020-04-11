""" Controller to execute histy_charts with arguments  """
# standard libs
from argparse import ArgumentParser
# app modules
from core import app, helper, config

parser = ArgumentParser()
parser.add_argument("-t", "--top",
                    dest="top",
                    type=int,
                    default=config.DEFAULT_CHART,
                    help=f"Number of entries to be displayed (default: {config.DEFAULT_CHART})")
parser.add_argument("-c", "--cli",
                    dest="cli",
                    default=False,
                    action="store_true",
                    help="Print charts to console if this argument is included")
args = parser.parse_args()

log = helper.get_logger()

log.info(f"Executing [{__file__}] with args {[(arg, getattr(args, arg)) for arg in vars(args)]}")

with app.History_Handler() as history:
    history.create_charts(top=args.top, cli=args.cli)

helper.close_logger()