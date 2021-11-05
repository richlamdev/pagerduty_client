from  pdpyras import APISession
import json
import datetime
import argparse
import os
import sys


def check_api_key():

    home = os.path.expanduser ('~')

    try:
        with open (home + "/.pd/client.json", "r") as clientfile:
            apikey = json.load (clientfile)
            token = apikey['pagerduty']
            return token
    except IOError:
        key = { "pagerduty" : "" }
        print ()
        print ("WARNING: User API file '~/.pd/client.json' not found.")
        print ()
        print ("PagerDuty access key is required.")
        print ()
        token = input ("Enter PagerDuty API key: ")
        key ["pagerduty"] = token

        if not os.path.exists (home + "/.pd"):
            os.mkdir (home + "/.pd", 0o700)
        with open (home + "/.pd/client.json", "w") as storekeyfile:
            json.dump (key, storekeyfile, ensure_ascii=False,sort_keys=True, indent=4)
        os.chmod (home + "/.pd/client.json", 0o600)

        return token


def main():

    api_token = check_api_key()

    session = APISession (api_token)


if __name__ == "__main__":
    main()
