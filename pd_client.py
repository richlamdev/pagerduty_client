from pdpyras import APISession
import json
import argparse
import sys
from pathlib import Path
import csv
from types import SimpleNamespace


class JSONObject():
    """
    Create an object from JSON.
    While not actually required; enables convenient reference to JSON values
    as object.
    """
    def default(json_data):
        return json.loads (json_data, object_hook = lambda d: SimpleNamespace(**d))


def get_esc_policies(session,args):
    """
    Get all escalation policy ids and write to file.
    """
    services = list(session.iter_all('/escalation_policies'))

    services_json = [] #convert to JSON with double quotes.
    for serv in range (len (services)):
        services_json.append (json.dumps(services[serv], indent=4))

    escs = []
    esc_name = []
    esc_id = []
    templist = []

    for serv in range (len (services_json)):
        escs.append (JSONObject.default(services_json[serv]))
        esc_name.append (escs[serv].name)
        esc_id.append (escs[serv].id)
        print (esc_name[serv] + "," + esc_id[serv])

    with open (args.filename.name, "w") as output_file:
        json.dump (services, output_file, indent=4)

    print ()
    print ("Full JSON data written to file: " + args.filename.name)
    print ()

    header = ["name", "escalation_id"]
    data = list (zip (esc_name, esc_id))
    write_csv_file(header,data,"ids_only_" + args.filename.name)

    print ()
    print ("Escalation names and ID's only, written to file: " + "ids_only_" 
          + args.filename.name)
    print ()


def get_vendors(session,args):
    """
    Get all vendor ids and write to file.
    """
    services = list(session.iter_all('/vendors'))

    services_json = []
    for serv in range (len (services)):
        services_json.append (json.dumps(services[serv], indent=4))

    vends = []
    vend_name = []
    vend_id = []

    for serv in range (len (services_json)):
        vends.append (JSONObject.default(services_json[serv]))
        vend_name.append (vends[serv].name)
        vend_id.append (vends[serv].id)
        print (vend_name[serv] + "," + vend_id[serv])

    with open (args.filename.name, "w") as output_file:
        json.dump (services, output_file, indent=4)

    print ()
    print ("Full JSON data written to file: " + args.filename.name)
    print ()

    header = ["name", "vendor_id"]
    data = list (zip (vend_name, vend_id))
    write_csv_file(header,data,"ids_only_" + args.filename.name)

    print ()
    print ("Vendor names and ID's only, written to file: " + "ids_only_" 
          + args.filename.name)
    print ()


def get_services (session, query):
    """
    Get integration points, according to query parameter
    Returns list of service objects (json format)
    """
    services = list(session.iter_all('services', params={'query': query} ))

    return services


def get_service_urls (all_services):
    """
    returns the service url to query to obtain integrations
    """
    integration_urls = []
    service_urls = []
    endpoint_url_only = []
    base_url = "https://api.pagerduty.com/"

    #print (json.dumps(all_services, indent=4))

    with open ("temp.csv", "w") as tempfile:
        json.dump (all_services, tempfile, indent=4)

    all_services_json = [] #convert to JSON with double quotes.
    for serv in range (len (all_services)):
        all_services_json.append (json.dumps(all_services[serv], indent=4))

    ints = []
    int_name = []
    int_id = []
    service_ints = []

    for serv in range (len (all_services_json)):
        ints.append (JSONObject.default(all_services_json[serv]))
        int_name.append (ints[serv].name)
        int_id.append (ints[serv].id)

        # Get all integrations, in case there is more than one
        for ints_with_service in range (len (ints[serv].integrations)):
            service_ints.append (ints[serv].integrations[ints_with_service].self)
            endpoint_url_only.append (service_ints[serv])

    #print ("total endpoint: " + str (len (endpoint_url_only)))

    return endpoint_url_only


def get_integration_keys (session, all_integrations):
    """
    obtains solarwindows integration key based on service URL.
    returns integration name and integration key
    """
    integration_info = []
    integration_keys = []
    integration_name = []

    for service in range (len(all_integrations)):
        integration_info.append (session.rget (all_integrations[service]))
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
    # identify services without integrations and remove
    for serv in range (len (all_services)):
        if not all_services[serv]["integrations"]:
            service_without_integration.append (serv)

    for serv in range (len (service_without_integration)):
        temp = service_without_integration[serv]
        print ("Removing service(s) to examine that have no integration:")
        print ("\t" +  all_services[temp]["name"])
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

    getvend_parser = subparsers.add_parser ('getvend',
        help="""get vendor ids; eg: python3 pd_client.py getvend
             <output_filename.csv>""",
        description="eg: python3 pd_client.py getkeys <output_filename.csv>")
    getvend_parser.add_argument ('filename', type=argparse.FileType('w'),
        help='get all vendor ids - csv output',
        metavar="filename")
    getvend_parser.set_defaults (func=get_vendors)

    getesc_parser = subparsers.add_parser ('getesc',
        help="""get escalation policy ids; eg: python3 pd_client.py getesc
             <output_filename.csv>""",
        description="eg: python3 pd_client.py getkeys <output_filename.csv>")
    getesc_parser.add_argument ('filename', type=argparse.FileType('w'),
        help='get all esclation ids - csv output',
        metavar="filename")
    getesc_parser.set_defaults (func=get_esc_policies)

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
