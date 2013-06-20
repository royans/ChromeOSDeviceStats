ChromeOS Device Reporting
=========================

* This script is useful only if you have ChromeOS devices enrolled into your Google Apps Domain.
*  Prerequisites
    - Google Apps Domain with ChromeOS management enabled
    - Devices should be enrolled into the domain
    - Google API Console
	- Create a project 
	- Enable Admin SDK
        - Create "Client ID for installed applications"
* Update client_secrets.json
* There are some python library dependencies
* How to run it
    - To get stats "python audit.py"
    - To dump all the devices in CSV format "python audit.py --csv=True"
