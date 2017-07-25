# pythonScripts
DevOps work for automated regression, dashboard, and notification tasks

Uses Python to automate tasks such as retrieving data from MS SQL Database, sending email notifications about disk usage, creating HTML reports, and modify/create labels to Perforce labels.



Summary:

Connects remote server running Microsoft SQL Server, queries the DB, and dispatches email alerts based on trigger.

This program requires python3 and pip module pymssql. It "may" require freetds or ODBC driver to connect to the DB but depending on your linux distro/version you may not need it. Also pip module json but should come as part of std lib in python 3.

To execute: % python3 -m pip install pymssql % ./trigger_reg_failing.py --project napier

Result: Queries DB and emails block owners when last x tests failed consecutively



Globals: set in config.py

DEBUG - expected to be 1,2,3 or 4. Only dispatches email when DEBUG < 2 When DEBUG set to 1, emails sent only to 'emailMeOnly' (set in config.py) Wehn bool(DEBUG) False (set to 0 or unset), emails are sent to block owners from json file

CONSECUTIVE_FAIL_TRIGGER - number of times test much fail consecutively in order to trigger email alert
