The _Demo-Transactionprocessor_ is basic web-application for processing transactions of cryptocurrencies.

## Usage
Call `run.sh` contained in the `/` directory:
 * Either creates a venv if installed python > 3.6 or local distribution
 * Installs the requirements into it
 * Runs the server via `hug`

## Required 3rd Party Packages
* jinja2
    - Templating engine used in the web-framework for the Frontend
* hug
    - Web-framework that provides the Endpoints
* sqlalchemy
    - Database abstraction layer
* validate_email
    - Format checking at user creation


## Endpoints

### WEB
* `/`
    * rendered web-application template
* `/static`
    * serves folder containing .js and .css files

### REST
* `/user`
    * _GET_
        * get all or just selected user(s) 
    * _POST_
        * create user
* `/add_account`
    * _POST_
        * add account to user
* `/add`
    * _POST_
        * add currency to user
* `/submit`
    * _POST_
        * add transaction
* `/history`
    * _GET_
        * get all transactions of user
* `/transaction`
    * _GET_
        * get state of selected transaction
