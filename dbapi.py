"""
This module contains the (REST-)endpoints

Endpoint requirements:
2. Implement the web application with the following endpoints / handlers
    a. Register basic user details
       - Validate and store details in database
    b. Add currency account (Bitcoin, Ethereum)
       - Validate and set account details
    c. Submit transaction
       - Put the transaction into transaction
         processor queue and return its transaction id
    d. Retrieve account history for user id
       - Retrieve list of all the processed transactions
         and their state, each entry consisting of amount,
         source user id, target user id and currency type
    e. Retrieve transaction status
"""
from datetime import datetime
from multiprocessing import Process, Queue
from queue import Empty
import time
import os

from jinja2 import FileSystemLoader, Environment
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
import hug
import validate_email

from log import logger
import transactiondatabase as db

transaction_queue = Queue()


@hug.post('/user')
def create_user(name: hug.types.text, description: hug.types.text,
                email: hug.types.text,
                max_per_transaction: hug.types.number,
                account_bitcoin: hug.types.text=None,
                account_ethereum: hug.types.text=None):
    if not validate_email.validate_email(email):
        return f'email was not valid - {email}'
    accounts = {}
    session = db.get_session()
    try:
        if account_bitcoin:
            acc = session.query(db.AccountBitcoin).filter(db.AccountBitcoin.id == account_bitcoin).first()
            if acc:
                return f'Account IDs have to be unique - {account_bitcoin}'
            accounts['account_bitcoin'] = db.AccountBitcoin(id=account_bitcoin)
        if account_ethereum:
            acc = session.query(db.AccountEthereum).filter(db.AccountEthereum.id == account_ethereum).first()
            if acc:
                return f'Account IDs have to be unique - {account_bitcoin}'
            accounts['account_ethereum'] = db.AccountEthereum(id=account_ethereum)

        user = db.User(name=name, description=description, email=email,
                       max_per_transaction=max_per_transaction, **accounts)
        session.add(user)
        session.commit()
        ret = user.as_dict()
    except IntegrityError as e:
        ret = str(e)
    finally:
        session.close()
    return ret


@hug.get('/user')
def get_user(user_id: hug.types.number=None):
    session = db.get_session()
    try:
        if user_id:
            user = session.query(db.User).filter(db.User.id == user_id).first()
            return user.as_dict() if user else None
        else:
            users = session.query(db.User).all()
            return [_.as_dict() for _ in users]
    finally:
        session.close()


@hug.post('/add_account')
def add_account(user_id: hug.types.number, account_id: hug.types.text, account_type: hug.types.text):
    account_cls = {
        'BTC': db.AccountBitcoin,
        'ETH': db.AccountEthereum
    }[account_type]
    account_in_user = {
        'BTC': 'account_bitcoin',
        'ETH': 'account_ethereum'
    }[account_type]

    session = db.get_session()
    try:
        user = session.query(db.User).filter(db.User.id == user_id).first()
        account = session.query(account_cls).filter(account_cls.id == account_id).first()
        if account:
            return f'Account IDs have to be unique <{account_id}>'
        elif not user:
            return f'No User with id <{user_id}> found'
        elif user.__getattribute__(account_in_user):
            return f'User already had such an account - {account_type}'
        else:
            account = account_cls(id=account_id, user_id=user_id)
            session.add(account)
            session.commit()
            ret = account.as_dict()
            return ret
    except IntegrityError as e:
        return str(e)
    finally:
        session.close()


@hug.post('/add')
def add_currency(user: hug.types.number, currency: hug.types.text, amount: hug.types.number):
    session = db.get_session()
    try:
        _user = session.query(db.User).filter(db.User.id == user).first()
        if not _user:
            return f'No such User - {user}'
        account = {
            'BTC': _user.account_bitcoin,
            'ETH': _user.account_ethereum
        }.get(currency, None)
        if not account:
            return f'No such Currency - {currency}'
        _user.add_currency(currency, amount)
        session.commit()
        ret = _user.as_dict()
        return ret
    finally:
        session.close()


@hug.post('/submit')
def submit_transaction(source: hug.types.text, target: hug.types.text,
                       currency: hug.types.text, amount: hug.types.number):
    account_type = {
        'BTC': 'account_bitcoin',
        'ETH': 'account_ethereum'
    }.get(currency, '')
    if not account_type:
        return f'No such Currency - {currency}'
    session = db.get_session()
    try:
        s = session.query(db.User).filter(db.User.id == source).first()
        t = session.query(db.User).filter(db.User.id == target).first()
        if not s or not t:
            return f'Both Users have to exist - {source}, {target}'
        if not getattr(s, account_type) or not getattr(t, account_type):
            return f'Both Users have to have Accounts of type - {currency}'
        transaction = db.Transaction(currency_amount=amount, currency_type=currency,
                                     source_user_id=source, target_user_id=target,
                                     timestamp_created = datetime.now())
        session.add(transaction)
        session.commit()
        ret = transaction.as_dict()
        logger.debug(ret)
        transaction_queue.put(ret['id'])
    finally:
        session.close()
    return ret


@hug.get('/history')
def get_transaction_history(user_id: hug.types.number):
    session = db.get_session()
    try:
        transactions = session.query(db.Transaction).filter(
            or_(
                db.Transaction.source_user_id == user_id,
                db.Transaction.target_user_id == user_id
            )
        ).all()
        ret = [_.as_dict() for _ in transactions]
    finally:
        session.close()
    return ret


@hug.get('/transaction')
def get_transaction(transaction_id: hug.types.number=None):
    session = db.get_session()
    try:
        if transaction_id:
            transaction = session.query(db.Transaction)\
                .filter(db.Transaction.id == transaction_id).first()
            return transaction.as_dict() if transaction else f'No such Transaction'
        else:
            transactions = session.query(db.Transaction).all()
            return [_.as_dict() for _ in transactions]
    finally:
        session.close()


@hug.get('/state')
def get_transaction_status(transaction_id: hug.types.number):
    session = db.get_session()
    try:
        transaction = session.query(db.Transaction)\
            .filter(db.Transaction.id == transaction_id).first()
        return transaction.state if transaction else f'No such Transaction'
    finally:
        session.close()


def transaction_processor():
    def process_one(session, transaction):
        transaction.state = 'PROCESSING'
        session.commit()
        logger.debug(transaction.as_dict())
        time.sleep(2)
        transaction.process()
        session.commit()
        logger.debug(transaction.as_dict())

    while True:
        session = db.get_session()
        try:
            transaction_id = transaction_queue.get(timeout=2)
            if not transaction_id:
                break
        except KeyboardInterrupt:
            break
        except Empty:
            transaction = session.query(db.Transaction).filter(db.Transaction.state == 'NEW').first()
            if transaction:
                process_one(session, transaction)
        else:
            transactions = session.query(db.Transaction).filter(and_(
                db.Transaction.id < transaction_id, db.Transaction.state == 'NEW')).all()
            for i in transactions:
                process_one(session, i)
            transaction = session.query(db.Transaction).filter(db.Transaction.id == transaction_id).first()
            if not transaction:
                continue
            process_one(session, transaction)
        finally:
            session.close()


process = Process(target=transaction_processor, daemon=True)
process.start()


template_engine = Environment(loader=FileSystemLoader("templates"))


@hug.get('/', output=hug.output_format.html)
def index(user_id: hug.types.number=None):
    template = template_engine.get_template("index.html")
    return template.render({'user_id': user_id if user_id else ''})


@hug.static('/static')
def static_dir():
    """Returns static directory names to be served."""
    directory = os.path.dirname(os.path.realpath(__file__))
    directory = os.path.join(directory, 'static')
    return (directory, )
