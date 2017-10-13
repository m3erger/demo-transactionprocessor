The _Demo-Transactionprocessor_ is basic web-application for processing transactions of cryptocurrencies.

## Usage
Call `run.sh` contained in the `/` directory:
 * It creates a local Python 3.6 distribution
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
