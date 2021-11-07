from  pdpyras import APISession
import json
import datetime
import argparse
import sys
from pathlib import Path
import re
import csv


def get_services (session, query):

    services = list(session.iter_all('services', params={'query': query} ))

    return services


def get_service_urls (all_services):

    integration_urls = []
    service_urls = []
    endpoint_url_only = []

    for service in range (len (all_services)):
        integration_urls.append ( dict (all_services[service]) )
        service_urls.append (json.dumps(integration_urls[service]["integrations"][0]["self"]))
        base_url = "https://api.pagerduty.com/"
        endpoint_url_only.append (re.sub (base_url,"",service_urls[service]))

    return endpoint_url_only


def get_integration_keys (session, all_integrations):

    integration_info = []
    integration_keys = []
    integration_name = []

    for service in range (len (all_integrations)):
        integration_info.append (session.rget (json.loads(all_integrations[service])))
        integration_name.append (integration_info[service]["service"]["summary"])

        if "integration_key" in integration_info[service]:
            integration_keys.append (integration_info[service]["integration_key"])
        else:
            integration_keys.append (0)

    return integration_name, integration_keys


def write_csv_file(header,data,filename):

    with open (filename, "w", encoding='UTF8', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow (header)
        writer.writerows (data)

def output_all_integration_keys(session,args):

    all_services = []
    integration_urls = []
    all_services = get_services(session, "*Network")
    integration_urls = get_service_urls (all_services)
    integration_name, integration_keys = get_integration_keys (session, integration_urls)
    header = ["name", "integration_key"]
    data = list (zip (integration_name, integration_keys))
    print (args.filename.name)
    write_csv_file(header,data,args.filename.name)

    pass


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


    parser = argparse.ArgumentParser (add_help=True,
             description="CLI interface for pagerduty API. \n\nView help page for each command for more information\n\n" +
             "python3 pd_client.py getkeys -h\n\npython3 pd_client.py setsvc -h\n\npython3 pd_client.py delsvc -h",
             formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers (help='commands', dest='subparser')

    getkeys_parser = subparsers.add_parser ('getkeys', help="get integration keys; eg: python3 pd_client.py getkeys <output_filename.csv>", description="eg: python3 pd_client.py getkeys <output_filename.csv>")
    getkeys_parser.add_argument ('filename', type=argparse.FileType('w'), help='get all integration keys from services - csv output', metavar="filename")
    getkeys_parser.set_defaults (func=output_all_integration_keys)

    setsvc_parser = subparsers.add_parser ('setsvc', help="create services; eg: python3 pd_client.py setsvc <input_filename.csv>", description="eg. python3 pd_client.py setsvc <input_filename.csv>\n\n")
    setsvc_parser.add_argument ('filename', type=argparse.FileType('r'), help='create services via file - service name,escalation policy name,integration_name', metavar="filename")
    #setsvc_parser.set_defaults (func=set_services)

    delsvc_parser = subparsers.add_parser ('delsvc', help="delete services; eg: python3 pd_client.py delsvc <input_filename.csv>", description="eg: python3 pd_client.py delsvc <input_filename.csv>\n\n")
    delsvc_parser.add_argument ('filename', type=argparse.FileType('r'), help='delete services via file - one servicename per line', metavar="filename")
    #delsvc_parser.set_defaults (func=del_services)

    args = parser.parse_args()

    # If there are no arguments to pass, aside from --help (-h) then display help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit()

    try:
        api_token = check_api_key()
        session = APISession (api_token)
        args.func (session, args)
    except AttributeError:
        parser.print_help()
        parser.exit()


if __name__ == "__main__":
    main()
