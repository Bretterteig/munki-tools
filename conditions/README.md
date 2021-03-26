## Conditions
### Description
These scripts extend munkis condtion catalog. Simply install them under /usr/local/munki/conditions.
Read more about conditions here: https://github.com/munki/munki/wiki/Conditional-Items


#### jamf_groups
This script users the JAMF classic API to extract the computer and group memberships of this computer and the main user (JAMF location attribute).
It needs two additional settings within the ManagedInstalls settings domain (Settings that configure Munki)

Add these two keys of type string:
- JAMF_API_USER
- JAMF_API_PASSWORD

The API users needs to be able to read users and computers.


It will create these condition arrays:
- JAMF_user_groups
- JAMF_computer_groups

Here is a sample condtion:
_JAMF_user_groups CONTAINS "MyGroup"_

#### language
This will output the language locale of the system in this format: en-EN
Be advised that combinations such as en-NL are possible.

It is advisable to create conditions like this:
_language BEGINSWITH en-_

#### console_user
This codition will make it possible to scope software to the currently logged in user.

Sample condition:
_current_user EQUALS "admin"_