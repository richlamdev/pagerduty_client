from  pdpyras import APISession
import json
import datetime
import argparse
import sys
from pathlib import Path
import re


def get_services (session, query):

    #session = APISession (api_token)
    services = list(session.iter_all('services', params={'query': query} ))
    #print (services)

    return services

def get_service_urls (all_services):

    integration_urls = []
    service_urls = []
    endpoint_url_only = []

    for service in range (len (all_services)):
        integration_urls.append ( dict (all_services[service]) )
        #print (json.dumps (integration_urls[service], indent=4, sort_keys=False))
        #print (json.dumps (integration_urls[service]["integrations"][0]["self"]))
        service_urls.append (json.dumps(integration_urls[service]["integrations"][0]["self"]))
        base_url = "https://api.pagerduty.com/"
        endpoint_url_only.append (re.sub (base_url,"",service_urls[service]))
        #print (endpoint_url_only[service])

    return endpoint_url_only

def get_integration_keys (session, all_integrations):

    #print (json.loads(integration_urls[0]))

    integration_info = []
    integration_keys = []
    integration_name = []

    for service in range (len (all_integrations)):
        integration_info.append (session.rget (json.loads(all_integrations[service])))
        #print (json.dumps(integration_info[service],indent=4))
        integration_name.append (integration_info[service]["service"]["summary"])
        print (integration_name[service])

        #integration_keys.append (integration_info[service]["integration_key"])
        #print (integration_keys[service])



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
    integration_urls = []

    api_token = check_api_key()
    #print (api_token)

    session = APISession (api_token)

    all_services = get_services(session, "*Network")

    integration_urls = get_service_urls (all_services)
    #print (integration_urls)

    get_integration_keys (session, integration_urls)


    #for service in all_services:
        #integration_urls[service] = 

    #for service in all_services:
        #print (service)

    #print ("number of services: " + str(len(all_services)) )


if __name__ == "__main__":
    main()
