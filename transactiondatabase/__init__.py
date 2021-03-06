from datetime import datetime

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers

# import or define all models here to ensure they are attached to the
# Base.metadata prior to any initialization routines
from .model import *

# run configure_mappers after defining all of the models to ensure
# all relationships can be setup
configure_mappers()

_engine = create_engine('sqlite:///sqlite.db', echo=False)
_session_factory = sessionmaker(bind=_engine)

Base.metadata.create_all(_engine)


def get_session():
    return _session_factory()


def prefill_db():
    session = get_session()
    if len(session.query(User).all()) > 0:
        session.close()
        return
    session.add_all([
        User(name='test1', description='desc.',
             email='te.st1@example.com', max_per_transaction=500,
             account_bitcoin=AccountBitcoin(id='001122334455', balance=50)),
        User(name='test2', description='des2.',
             email='qw.er1234@gmail.com', max_per_transaction=3,
             account_bitcoin=AccountBitcoin(id='aabbccddee')),
        Transaction(currency_type='BTC', currency_amount=1,
                    source_user_id='1', target_user_id='2',
                    timestamp_created=datetime.now(), state='NEW'),
        Transaction(currency_type='BTC', currency_amount=1,
                    source_user_id='1', target_user_id='2',
                    timestamp_created=datetime.now(), state='ERROR'),
        Transaction(currency_type='BTC', currency_amount=1,
                    source_user_id='1', target_user_id='2',
                    timestamp_created=datetime.now(), state='DONE'),
    ])
    session.commit()
    session.close()


prefill_db()
