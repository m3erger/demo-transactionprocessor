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

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import hug


import transactiondatabase as db


@hug.post('/user')
def create_user(name: hug.types.text, description: hug.types.text, email: hug.types.text,
                max_per_transaction: hug.types.number,
                account_bitcoin: hug.types.text=None,
                account_ethereum: hug.types.text=None):
    accounts = {}
    session = db.get_session()
    if account_bitcoin:
        acc = session.query(db.AccountBitcoin).filter(db.AccountBitcoin.id == account_bitcoin).first()
        if acc:
            session.close()
            return f'Account IDs have to be unique - {account_bitcoin}'
        accounts['account_bitcoin'] = db.AccountBitcoin(id=account_bitcoin)
    if account_ethereum:
        acc = session.query(db.AccountEthereum).filter(db.AccountEthereum.id == account_ethereum).first()
        if acc:
            session.close()
            return f'Account IDs have to be unique - {account_bitcoin}'
        accounts['account_ethereum'] = db.AccountEthereum(id=account_ethereum)
    ret = None
    try:
        user = db.User(name=name, description=description, email=email,
                       max_per_transaction=max_per_transaction, **accounts)
        session.add(user)
        ret = user.as_dict()
        session.commit()
    except IntegrityError as e:
        ret = str(e)
    finally:
        session.close()
    return ret


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
    user = session.query(db.User).filter(db.User.id == user_id).first()
    account = session.query(account_cls).filter(account_cls.id == account_id).first()
    ret = None
    try:
        if account and user:
            ret = f'Account IDs have to be unique <{account_id}>'
        elif not user:
            ret = f'No User with id <{user_id}> found'
        elif user.__getattribute__(account_in_user):
            ret = f'User already had such an account - {account_type}'
        else:
            account = account_cls(id=account_id, user_id=user_id)
            session.add(account)
            ret = account.as_dict()
            session.commit()
    except IntegrityError as e:
        ret = str(e)
    finally:
        session.close()
    return ret


@hug.post('/add')
def add_currency(user: hug.types.number, currency: hug.types.text, amount: hug.types.number):
    session = db.get_session()
    _user = session.query(db.User).filter(db.User.id == user).first()
    if not _user:
        session.close()
        return f'No such User - {user}'
    account = {
        'BTC': _user.account_bitcoin,
        'ETH': _user.account_ethereum
    }.get(currency, None)
    if not account:
        session.close()
        return f'No such Currency - {currency}'
    _user.add_currency(currency, amount)
    ret = _user.as_dict()
    session.commit()
    session.close()
    return ret


@hug.post('/submit')
def submit_transaction(source: hug.types.text, target: hug.types.text,
                       currency: hug.types.text, amount: hug.types.number):
    account_type = {
        'BTC': 'account_bitcoin',
        'ETH': 'account_ethereum'
    }.get(currency, '')
    session = db.get_session()
    s = session.query(db.User).filter(db.User.id == source).first()
    t = session.query(db.User).filter(db.User.id == target).first()
    if not s or not t:
        session.close()
        return f'Both Users have to exist - {source}, {target}'
    if not getattr(s, account_type) or not getattr(t, account_type):
        session.close()
        return f'Both Users have to have Accounts of type - {currency}'
    transaction = db.Transaction(currency_amount=amount, currency_type=currency,
                                 source_user_id=source, target_user_id=target,
                                 timestamp_created = datetime.now())
    session.add(transaction)
    session.commit()
    ret = transaction.as_dict()
    session.close()
    return ret


@hug.get('/users')
def get_users():
    session = db.get_session()
    users = session.query(db.User).all()
    ret = [_.as_dict() for _ in users]
    session.close()
    return ret


@hug.get('/user')
def get_transactions_of_user(id: hug.types.number):
    session = db.get_session()
    transactions = session.query(db.Transaction).filter(
        or_(
            db.Transaction.source_user_id == id,
            db.Transaction.target_user_id == id
        )
    ).all()
    ret = [_.as_dict() for _ in transactions]
    session.close()
    return ret


@hug.get('/transaction')
def get_transaction_status(id: hug.types.number):
    session = db.get_session()
    transaction = session.query(db.Transaction)\
        .filter(db.Transaction.id == id).first()
    session.close()
    if transaction:
        return transaction.state
    return f'No such Transaction'
