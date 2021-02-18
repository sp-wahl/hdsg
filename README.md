# hdsg
Hast du schon gewählt?

A software to check whether people have already voted in vote by mail student parliament elections.

## Where to use this software

**Do not run this software with live data on a machine that is connected to the Internet.**

It has not been built for that purpose, and is not fit to saveguard the data it handles from attacks.

Only run this software in a setting where the machine this software runs on and the clients that access it are in a local network separated from the outside world.

## How to use this software

1. Set up a mariadb database
2. Adapt the configuration in `config.py`. Especially choose a different random `SECRET_KEY` value.
3. Run this python application with some kind of server that is fit for the purpose (e.g. gunicorn). 
4. Import a list of users with passwords using the script `setup.py`
5. Import your list of voters with the script `setup.py`
6. Connect to the running server from your clients using a web browser, log in using the imported user/password combinations, and start scanning and marking ids

### Demo mode

You can login using `demo` as username and password, which activates a demo mode that can be used for demonstrating the different scenarios to prospective users.

The id 11111 yields a regular person that can be marked an infinite amount of times,  
the id 22222 yields a person that has been marked as having a second edition of their id card,  
the id 33333 yields a person that has already been marked as having voted,  
and any other id yields a message that no result has been found.

Just reload the page to get out of demo mode again.

## Setup

```
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running tests

```
PYTHONPATH=. pytest
```

## Running (development)

```
source venv/bin/activate
./main.py
```
