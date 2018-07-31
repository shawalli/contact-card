# Contact Card
This project demonstrates the interaction between a Heroku app and Salesforce,
using Heroku Connect. The app is a single-file Python Flask application.

# Setup Instructions
This project assumes that you have a
[Salesforce Developer Edition environment](https://developer.salesforce.com/signup)
and a [Heroku account](https://signup.heroku.com). Once those pre-requisites
are met, follow the instructions below.

## Deploy The Heroku App
*These instructions will create a Heroku app, deploy this project into the app,
and configure the app.*

1. Click the `Deploy to Heroku` button below. You will be directed to a Heroku
   app deployment page. If you'd like to keep these instructions open,
   right-click on the button and click `Open Link in New Tab` instead.

   [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/shawalli/contact-card)

1. Choose a unique name for your app. If you leave it blank, Heroku will
   generate a unique name for you.

1. Click the `Deploy app` button at the bottom of the screen.

1. Once the build and deployment are complete, click the `View` button at the
   bottom of the screen.

## Configure Heroku Connect Connection
*These instructions will connect the app's Heroku Connect add-on to your
desired Salesforce environment.*

1. On the welcome page of your app, click the `Connect Salesforce Environment`
   button. Keep this tab open.

1. On the Heroku dashboard page for your app, click the Heroku Connect row in
   the Add-ons table.

1. Click the `Setup Connection` button in the upper-left corner.

1. The `DATABASE_URL` row within the Database Config Vars table should be
   highlighted. Click the row anyway (Heroku cannot detect that it is
   auto-selected for some reason). Your app expects the schema to be named
   "salesforce", so leave that setting alone.

1. Click the `Next` button in the upper-right corner.

1. The environment should be set to `Production` and the API version should be
   set to the latest Salesforce version. At the time of this writing, the
   latest API version is `43.0`. Click the `Authorize` button in the
   upper-right corner.

1. Type in the username and password for your Salesforce Developer Edition
   environment to which you'd like to connect. Click the `Log In` button.

1. Once the environment has been authorized, you should be redirected back to
   Heroku, on your Heroku Connect add-on page. Keep this tab open.

## Configure Salesforce Environment.
*These steps will ensure that your Salesforce environment can receive record
changes from the Heroku app. A new field is created that is used by Heroku
during the write-to-Salesforce process.*

1. Login to your Salesforce environment (most likely, you will use
   [login.salesforce.com](https://login.salesforce.com)).

1. Open the Setup Menu. This is done by clicking the gear in the upper-right
   corner, then clicking the `Setup` dropdown.

1. Click the "Object Manager" tab.

1. Click the `Contact` link in the Contact row.

1. Click the "Fields & Relationships" tab in the sidebar.

1. Click the `New` button in the upper-right corner.

1. Select the `Text` radio button.

1. Click the `Next` button in the lower-right corner.

1. Use the following settings:
   - **Field Label**: External Contact Id
   - **Length**: 32
   - **Field Name**: External_Contact_Id
   - **Description**: This field is used by Heroku Connect to sync changes back to
                      Salesforce. It should never be modified within Salesforce.
   - **Help Text**: This is an internal field. You probably don't want to change
                    this value.
   - **Required**: Leave unchecked
   - **Unique**: Check. Ensure the "Treat ABC and abc as duplicate values (case
                 insensitive") radio button is selected.
   - **External ID**: Check
   - **Default Value**: Leave blank

1. Click the `Next` button in the lower-right corner.

1. Click the `Visible` column checkbox at the top of the table twice to
   select-all profiles, then de-select-all profiles. Select visibility for:
   - Standard Platform User
   - Standard User
   - System Administrator

1. Ensure no profiles in the `Read-Only` column are checked.

1. Click the `Next` button in the lower-right corner.

1. Click the `Add Field` column checkbox at the top of the table to
   de-select-all layouts. Then, select only the "Contact layout" row.

1. Click the `Save` button in the lower-right corner.

## Configure Heroku Connect Mapping
*These steps will map your Salesforce environment Contact sObject to the Heroku
app's PostGreSQL database.*

1. Return to the tab with your app's Heroku Connect add-on page. Click the
   "Mappings" tab.

1. Click the `+Create Mapping` button in the lower-right corner.

1. Select the "Contact" row from the table of sObjects.

1. In the "Salesforce -> Database" section, check the `Accelerate Polling`
   checkbox.

1. In the "Database -> Salesorce" section, check the
   `Write database updates...` checkbox. From that setting's dropdown,
   select `External_Contact_Id__c` as the unique identifier.

1. In the "Mapped Fields" section, ensure the following fields are checked
   (It is OK if additional fields are selected due to Heroku Connect
   auto-selecting them):
   - Email
   - FirstName
   - LastName
   - Phone
   - Title

1. Click the `Save` button in the upper-right corner.

1. After a short time, the Heroku Connect mapping you just created should
   register a number of mapped fields, SF rows, and DB rows.

## Use Your App
1. Return to the tab that has your app and refresh the page. You should now
   see a table containing contacts from your environment!

1. To view a contact, select their contact row.

1. To edit a contact, change the contact's information and click the `Save`
   button. You should receive confirmation that the record was saved into the
   database.

1. To verify that the change was synced, login to your Salesforce environment.
   Click the "Contacts" tab and locate the contact that you changed. Verify
   that the information was updated.
