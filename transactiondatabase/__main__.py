from pprint import pprint

from . import *


prefill_db()

session = get_session()

pprint(session.query(User).all())
pprint(session.query(AccountBitcoin).all())

session.close()
