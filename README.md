# PagerDuty client 

## Introduction

This is a basic CLI PagerDuty client.  This was written with narrow scope of functionality.  Limited capabilities include:

1) Reading all services and associated integration keys, output to CSV file.\
2) Creating services via CSV input file.\
3) Delete services.  (To be implemented).\
4) Get all vendor ID numbers and output to CSV file.\
5) Get all escalation policy ID numbers and output to CSV file.\


## Requirements

1) Linux or Mac Operating System. Likely to will work on Windows, however untested.\
2) Python3.  May work with Python2, but not recommended and is also untested.\
3) API key for PagerDuty.\


## Basic Usage

### Obtain existing services with integration keys:

python3 pd_client.py getkeys <output_filename>

eg:
````python3 pd_client.py getkeys allkeys.csv````

### Set services with SolarWinds integration keys:

python3 pd_client.py setsvc <input_filename>

eg:
````python3 pd_client.py setsvc set_input.csv````

Format of input file is:

Name, Description, Escalation Policy ID, Vendor ID


### Remove existing services 

TBC - not yet inmplemented


### Get Vendor ID's:

python3 pd_client.py getvend <output_filename>

eg:
````python3 pd_client.py getvend vend_ids.csv````


### Get Escalation Policy ID's:

python3 pd_client.py getesc <output_filename>

eg:
````python3 pd_client.py getesc esc_ids.csv````
