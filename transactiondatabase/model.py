"""
This module contains the database table definitions for the application.

Database requirements:
    a. User - should consist of at least the following
                   - Identifier
                   - Name (max length is 512 characters)
                   - Description      (max length is 1k characters)
                   - E-Mail (max length is 1k characters)
                   - Account Id Bitcoin (max length of Bitcoin Account Id)
                   - Account balance Bitcoin (max value 1 bln)
                   - Account Id Ethereum (max length of Ethereum Account Id)
                   - Account balance Ethereum (max value 1 bln)
                   - Max amount per transaction
    b. Transaction
                   - Identifier
                   - Currency Amount
                   - Currency Type
                   - Source user id
                   - Target user id
                   - Timestamp created
                   - Timestamp processed
                   - State
"""
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship

from .meta import Base


class User(Base):
    """Relationships:
    1:1 to bitcoin account
    1:1 to ethereum account
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(512))
    description = Column(String(1000))
    email = Column(String(1000), unique=True)
    max_per_transaction = Column(Integer)

    account_bitcoin = relationship('AccountBitcoin', uselist=False, back_populates='user', lazy='subquery')
    account_ethereum = relationship('AccountEthereum', uselist=False, back_populates='user', lazy='subquery')

    def __repr__(self):
        return (
            f'<User(id={self.id}, name={self.name}, email={self.email}, '
            f'BTC={self.account_bitcoin}, ETH={self.account_ethereum}, '
            f'max_per_transaction={self.max_per_transaction})>'
        )

    def as_dict(self):
        ret = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'email': self.email,
            'max_per_transaction': self.max_per_transaction,
            'account_bitcoin': None,
            'account_ethereum': None
        }
        if self.account_bitcoin:
            ret['account_bitcoin'] = self.account_bitcoin.as_dict()
        if self.account_ethereum:
            ret['account_ethereum'] = self.account_ethereum.as_dict()
        return ret

    def add_currency(self, account_type, amount):
        account = {
            'BTC': self.account_bitcoin,
            'ETH': self.account_ethereum
        }[account_type]
        account.balance += amount


class AccountBitcoin(Base):
    """ address <= 34 char string
    https://en.bitcoin.it/wiki/Address#What.27s_in_an_address
    Relationships:
    1:1 to user
    """
    __tablename__ = 'accountbitcoin'

    id = Column(String(34), primary_key=True)
    balance = Column(BigInteger, default=0)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='account_bitcoin')

    __table_args__ = (
        CheckConstraint('balance<1000000000', name='check_balance'),
    )

    def __repr__(self):
        return f'<AccountBitcoin(id={self.id}, user_id={self.user_id}, balance={self.balance})>'

    def as_dict(self):
        return {
            'id': self.id,
            'balance': self.balance,
        }


class AccountEthereum(Base):
    """ address = 40 char string
    http://ethdocs.org/en/latest/glossary.html
    https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md#rationale
    Relationships:
    1:1 to user
    """
    __tablename__ = 'accountethereum'

    id = Column(String(40), primary_key=True)
    balance = Column(BigInteger, default=0)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='account_ethereum')

    __table_args__ = (
        CheckConstraint('balance<1000000000', name='check_balance'),
    )

    def __repr__(self):
        return f'<AccountBitcoin(id={self.id}, user_id={self.user_id}, balance={self.balance})>'

    def as_dict(self):
        return {
            'id': self.id,
            'balance': self.balance,
        }


class Transaction(Base):
    """Relationships:
    1:1 for source / target user
    """
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True)
    currency_amount = Column(BigInteger)
    currency_type = Column(String)

    source_user_id = Column(Integer, ForeignKey('user.id'))
    target_user_id = Column(Integer, ForeignKey('user.id'))
    source_user = relationship('User', foreign_keys=[source_user_id])
    target_user = relationship('User', foreign_keys=[target_user_id])

    timestamp_created = Column(TIMESTAMP, nullable=False)
    timestamp_processed = Column(TIMESTAMP, nullable=True)

    state = Column(String, default='NEW')

    def __repr__(self):
        return (
            f'<Transaction(id={self.id}, '
            f'currency_type={self.currency_type}, currency_amount={self.currency_amount}, '
            f'source={self.source_user_id}, target={self.target_user_id}, '
            
            f'created={self.timestamp_created}, processed={self.timestamp_processed}, '
            f'state={self.state})>'
        )

    def as_dict(self):
        return {
            'id': self.id,
            'currency_type': self.currency_type,
            'currency_amount': self.currency_amount,
            'source_user_id': self.source_user_id,
            'target_user_id': self.target_user_id,
            'state': self.state
        }

    def _get_user_accounts(self):
        try:
            wallet_type = {
                'BTC': 'account_bitcoin',
                'ETH': 'account_ethereum'
            }[self.currency_type]
        except KeyError:
            raise TransactionException(f'Unsupported CryptoCurrency: {self.currency_type}')
        else:
            source = self.source_user.__getattribute__(wallet_type)
            target = self.target_user.__getattribute__(wallet_type)
            return source, target

    def process(self):
        if self.state != 'PROCESSING':
            return
        try:
            source, target = self._get_user_accounts()
            if not source or not target:
                raise TransactionException(f'Source or Target User had no matching Currency Account')
            if source.balance < self.currency_amount:
                raise TransactionException(
                    f'User had not enough money ({source.balance} < {self.currency_amount})')
            if self.source_user.max_per_transaction < self.currency_amount:
                raise TransactionException(
                    f'Send limit reached ({self.currency_amount} > {self.source_user.max_per_transaction})')
            if target.balance + self.currency_amount > 1000000000:
                raise TransactionException(
                    f'Target would reach currency limit')
            source.balance -= self.currency_amount
            target.balance += self.currency_amount
            self.state = 'DONE'
        except TransactionException as e:
            self.state = f'ERROR - {str(e)}'


class TransactionException(Exception):
    pass
