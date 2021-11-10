from  pdpyras import APISession
import json
import argparse
import sys
from pathlib import Path
import csv


def get_services (session, query):
    """
    Get integration points, according to query parameter
    Returns list of service objects (json format)
    """

    services = list(session.iter_all('services', params={'query': query} ))

    return services


def get_service_urls (all_services):
    """
    returns the service url to query to obtain the integration key
    """
    integration_urls = []
    service_urls = []
    endpoint_url_only = []
    base_url = "https://api.pagerduty.com/"

    for service in range (len (all_services)):
        integration_urls.append ( dict (all_services[service]) )
        service_urls.append (json.dumps(integration_urls[service]
                            ["integrations"][0]["self"]))
        endpoint_url_only.append (service_urls[service].replace(base_url,''))

    return endpoint_url_only


def get_integration_keys (session, all_integrations):
    """
    obtains solarwindows integration key based on service URL.
    returns integration name and integration key
    """
    integration_info = []
    integration_keys = []
    integration_name = []

    for service in range (len (all_integrations)):
        integration_info.append (session.rget (json.loads(all_integrations
                                [service])))
        integration_name.append (integration_info[service]["service"]
                                ["summary"])

        if "integration_key" in integration_info[service]:
            integration_keys.append (integration_info[service]
                                    ["integration_key"])
        else:
            integration_keys.append (0)

    return integration_name, integration_keys


def write_csv_file(header,data,filename):
    """
    writes data to csv file per input filname
    """

    with open (filename, "w", encoding='UTF8', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow (header)
        writer.writerows (data)


def output_all_integration_keys(session,args):
    """
    Get all services, discard services without any integrations.
    Limited to only one integration key at this time.
    """
    all_services = get_services(session, "")

    service_without_integration = []

    for service in range (len (all_services)):
        if not all_services[service]["integrations"]:
            service_without_integration.append (service)

    for x in range (len (service_without_integration)):
        temp = (service_without_integration[x])
        print ("removing service to exam " + all_services[temp]["name"]
              + " as it has no integration")
        del all_services[temp]

    integration_urls = get_service_urls (all_services)
    integration_name, integration_keys = get_integration_keys(session,
                                                             integration_urls)
    header = ["name", "integration_key"]
    data = list (zip (integration_name, integration_keys))
    write_csv_file(header,data,args.filename.name)
    print ("Output file saved as: " + args.filename.name)


def set_services (session,args):
    """
    Create service with solarwinds integration according to input csv file.
    Currently limited to solarwinds integration.
    """
    with open (args.filename.name, 'r') as inputcsv:
        csv_reader = csv.DictReader (inputcsv, delimiter=',')
        data = {}
        for row in csv_reader:
            for header, value in row.items():
                try:
                    data[header].append(value)
                except KeyError:
                    data[header] = [value]

    name = data ['name']
    description = data ['description']
    esc_policy_id = data ['esc_policy_id']
    vendor_id = data ['vendor_id']

    for service_record in range (len(name)):

        payload = {
            "name": name[service_record],
            "description": description[service_record],
            "alert_creation": "create_alerts_and_incidents",
            "escalation_policy": {
                "id": esc_policy_id[service_record],   # requires specific escalation ID
                "type": "escalation_policy_reference"
            },
        }

        create_service = session.rpost ('services', json=payload)
        integration_path = '/services/' + create_service['id'] + '/integrations'

        # query services to review newly created service(s)
        #services = list(session.iter_all('services', params={'query': '*zz'})
        #print (json.dumps(services, indent=4))

        solar_int_payload = {
            "type": "events_api_v2_inbound_integration",
            "name": "SolarWinds Orion",
            "vendor": { "type": "vendor_reference", "id": vendor_id[service_record] }
        }                                                 #SolarWinds ID

        solar_integration = session.rpost (integration_path,
                                           json=solar_int_payload)

    # needed later for datadog integration
    #datadog_int_payload = {
        #"type": "events_api_v2_inbound_integration",
        #"name": "Datadog",
        #"vendor": { "type": "vendor_reference", "id": "PAM4FGS"} #Datadog ID
    #}
    #solar_integration = session.rpost (integration_path,
                                       #json=datadog_int_payload)


def check_api_key():
    """
    Checks for presence of API key in user home folder ~/.pd/client.json
    If API key is not present, prompts user for key and stores it.
    """
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
            json.dump (key, keyfile, ensure_ascii=False, indent=4)

        pd_api_file = Path (pd_api_file)
        pd_api_file.chmod (0o600)

        return token


def main():
    """
    Parse command line arguments by argparse
        getkeys - get all integration keys
        setsvc - create service
        delsv - delete server - to be implemented
    """

    parser = argparse.ArgumentParser (add_help=True,
             description="""CLI interface for pagerduty API.
             \n\nView help page for each command for more information
             \n\n" + "python3 pd_client.py getkeys -h
             \n\npython3 pd_client.py setsvc -h
             \n\npython3 pd_client.py delsvc -h""",
             formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers (help='commands', dest='subparser')

    getkeys_parser = subparsers.add_parser ('getkeys',
        help="""get integration keys; eg: python3 pd_client.py getkeys
             <output_filename.csv>""",
        description="eg: python3 pd_client.py getkeys <output_filename.csv>")
    getkeys_parser.add_argument ('filename', type=argparse.FileType('w'),
        help='get all integration keys from services - csv output',
        metavar="filename")
    getkeys_parser.set_defaults (func=output_all_integration_keys)

    setsvc_parser = subparsers.add_parser ('setsvc',
        help="""create services; eg: python3 pd_client.py setsvc
             <input_filename.csv>""",
        description="eg. python3 pd_client.py setsvc <input_filename.csv>\n\n")
    setsvc_parser.add_argument ('filename', type=argparse.FileType('r'),
        help='create services via file - name,escalation policy id',
        metavar="filename")
    setsvc_parser.set_defaults (func=set_services)

    delsvc_parser = subparsers.add_parser ('delsvc',
        help="""delete services; eg: python3 pd_client.py delsvc
              <input_filename.csv>""",
        description="eg: python3 pd_client.py delsvc <input_filename.csv>\n\n")
    delsvc_parser.add_argument ('filename', type=argparse.FileType('r'),
        help='delete services via file - one servicename per line',
        metavar="filename")
    #delsvc_parser.set_defaults (func=del_services)

    args = parser.parse_args()

    try:
        api_token = check_api_key()
        session = APISession (api_token)
        args.func (session, args)
    except AttributeError:
        parser.print_help()
        parser.exit()


if __name__ == "__main__":
    main()
