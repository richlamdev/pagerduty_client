from  pdpyras import APISession
import json
import datetime
import argparse
import sys
from pathlib import Path
import re


def get_services(api_token, query):

    session = APISession (api_token)
    services = list(session.iter_all('services', params={'query': query} ))
    #print (services)
    services_dict = dict (services[0])
    print (json.dumps(services_dict, indent=4, sort_keys=False))
    print ()
    print ()
    print ()

    print (json.dumps(services_dict["integrations"][0]["self"]))

    service_url = json.dumps(services_dict["integrations"][0]["self"])

    base_url = "https://api.pagerduty.com/"

    endpoint_url_only = re.sub (base_url,"",service_url)

    print (endpoint_url_only)

    print ()

    print ()
    print ()

    return services

    #with open ("temp.json", "w") as tempfile:
        #json.dump (services, tempfile, ensure_ascii=False,sort_keys=True, indent=4)

def check_api_key():

    home = str(Path.home())
    pd_folder = Path (home + "/.pd")
    pd_api_file = str(pd_folder) + "/client.json"

    try:
        with open (pd_api_file, "r") as clientfile:
            apikey = json.load (clientfile)
            token = apikey["pd_api_key"]
            return token

    except IOError:
        key = { "pd_api_key" : "" }
        print ()
        print ("WARNING: User API file " + pd_api_file + " not found.")
        print ()
        print ("PagerDuty access key is required.")
        print ("This will be stored at " + pd_api_file)
        print ()
        token = input ("Enter PagerDuty API key: ")
        key ["pd_api_key"] = token


        if not pd_folder.exists():
            pd_folder.mkdir (0o700, exist_ok=False)

        with open (pd_api_file, "w") as keyfile:
            json.dump (key, keyfile, ensure_ascii=False,sort_keys=True, indent=4)

        pd_api_file = Path (pd_api_file)
        pd_api_file.chmod (0o600)

        return token


def main():

    all_services = []

    api_token = check_api_key()
    #print (api_token)

    all_services = get_services(api_token, "*ETS")

    for service in all_services:
        print (service)

    print ("number of services: " + str(len(all_services)) )


if __name__ == "__main__":
    main()
