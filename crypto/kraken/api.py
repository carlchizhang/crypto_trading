# This file is part of krakenex.
#
# krakenex is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# krakenex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser
# General Public LICENSE along with krakenex. If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> and
# <http://www.gnu.org/licenses/gpl-3.0.txt>.

"""Kraken.com cryptocurrency Exchange API."""

import requests
import threading
import logging
import datetime
import statistics

# private query nonce
import time

# private query signing
import urllib.parse
import hashlib
import hmac
import base64

from . import version

RATE_LIMIT_EXCEEDED = ["EAPI:Rate limit exceeded"]
API_RATE_DECREMENT_TIMER = 3


class RateLimitError(Exception):
    pass


class API(object):
    """ Maintains a single session between this machine and Kraken.

    Specifying a key/secret pair is optional. If not specified, private
    queries will not be possible.

    The :py:attr:`session` attribute is a :py:class:`requests.Session`
    object. Customise networking options by manipulating it.

    Query responses, as received by :py:mod:`requests`, are retained
    as attribute :py:attr:`response` of this object. It is overwritten
    on each query.

    .. note::
       No query rate limiting is performed.

    """

    def __init__(self, key="", secret=""):
        """ Create an object with authentication information.

        :param key: (optional) key identifier for queries to the API
        :type key: str
        :param secret: (optional) actual private key used to sign messages
        :type secret: str
        :returns: None

        """
        self.key = key
        self.secret = secret
        self.uri = "https://api.kraken.com"
        self.apiversion = "0"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "krakenex/"
                + version.__version__
                + " (+"
                + version.__url__
                + ")"
            }
        )
        self.response = None
        self._json_options = {}
        self._call_counter = 0
        self._max_call_counter = 15
        self._decrement_counter()
        return

    def _increment_counter(self, method):
        m = {"Ledgers": 2, "TradesHistory": 2, "AddOrder": 0, "CancelOrder": 0}
        count = 1
        if method in m:
            count = m[method]
        self._call_counter += count

    def _decrement_counter(self):
        self._call_counter -= 1
        if self._call_counter < 0:
            self._call_counter = 0
        self._dtimer = threading.Timer(
            API_RATE_DECREMENT_TIMER, self._decrement_counter
        )
        self._dtimer.daemon = True
        self._dtimer.start()

    def at_api_limit(self):
        return self._call_counter >= self._max_call_counter

    def json_options(self, **kwargs):
        """ Set keyword arguments to be passed to JSON deserialization.

        :param kwargs: passed to :py:meth:`requests.Response.json`
        :returns: this instance for chaining

        """
        self._json_options = kwargs
        return self

    def close(self):
        """ Close this session.

        :returns: None

        """
        self.session.close()
        return

    def load_key(self, path):
        """ Load key and secret from file.

        Expected file format is key and secret on separate lines.

        :param path: path to keyfile
        :type path: str
        :returns: None

        """
        with open(path, "r") as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
        return

    def _query(self, urlpath, data, headers=None, timeout=None):
        """ Low-level query handling.

        .. note::
           Use :py:meth:`query_private` or :py:meth:`query_public`
           unless you have a good reason not to.

        :param urlpath: API URL path sans host
        :type urlpath: str
        :param data: API request parameters
        :type data: dict
        :param headers: (optional) HTTPS headers
        :type headers: dict
        :param timeout: (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :type timeout: int or float
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        :raises: :py:exc:`requests.HTTPError`: if response status not successful

        """
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = self.uri + urlpath

        self.response = self.session.post(
            url, data=data, headers=headers, timeout=timeout
        )

        if self.response.status_code not in (200, 201, 202):
            self.response.raise_for_status()

        error = self.response.json()["error"]
        if error:
            if error == RATE_LIMIT_EXCEEDED:
                raise RateLimitError(error)
            else:
                raise RuntimeError(error)

        return self.response.json(**self._json_options)["result"]

    def query_public(self, method, data=None, timeout=None):
        """ Performs an API query that does not require a valid key/secret pair.

        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :param timeout: (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :type timeout: int or float
        :returns: :py:meth:`requests.Response.json`-deserialised Python object

        """
        if data is None:
            data = {}

        urlpath = "/" + self.apiversion + "/public/" + method

        self._increment_counter(method)
        return self._query(urlpath, data, timeout=timeout)

    def query_private(self, method, data=None, timeout=None):
        """ Performs an API query that requires a valid key/secret pair.

        :param method: API method name
        :type method: str
        :param data: (optional) API request parameters
        :type data: dict
        :param timeout: (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :type timeout: int or float
        :returns: :py:meth:`requests.Response.json`-deserialised Python object

        """
        if data is None:
            data = {}

        if not self.key or not self.secret:
            raise Exception("Either key or secret is not set! (Use `load_key()`.")

        data["nonce"] = self._nonce()

        urlpath = "/" + self.apiversion + "/private/" + method

        headers = {"API-Key": self.key, "API-Sign": self._sign(data, urlpath)}

        self._increment_counter(method)
        return self._query(urlpath, data, headers, timeout=timeout)

    def _nonce(self):
        """ Nonce counter.

        :returns: an always-increasing unsigned integer (up to 64 bits wide)

        """
        return int(1000 * time.time())

    def _sign(self, data, urlpath):
        """ Sign request data according to Kraken's scheme.

        :param data: API request parameters
        :type data: dict
        :param urlpath: API URL path sans host
        :type urlpath: str
        :returns: signature digest
        """
        postdata = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data["nonce"]) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        return sigdigest.decode()

    def get_orderbook(self, pair):
        while self.at_api_limit():
            pass

        try:
            r = self.query_public("Depth", data={"pair": pair})
        except RateLimitError:
            logging.warning("Rate limit hit...")
            return None

        logging.info(
            "Order books as of time %s for pair %s", str(datetime.datetime.now()), pair
        )
        logging.info(
            "Bid mean: %f",
            statistics.mean([float(item[0]) for item in r[pair]["bids"]]),
        )
        logging.info(
            "Ask mean: %f",
            statistics.mean([float(item[0]) for item in r[pair]["asks"]]),
        )
        return r[pair]
