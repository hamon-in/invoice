## Environment variables
   - `INVOICE_DB` - Location of database file

This is a command line tool to manage invoices for a small company. We can manage the different parts of software using subcommands. They are listed below.
1. init : Init Commands
1. db : DB commands 
1. Summary : Summary commands 
1. Timesheet : Timesheet commands
1. Account : Account commands 
1. Client : Client commands
1. Template : Template commands
1. Invoice : Invoice commands
1. Tag : Tag commands 

## Init 
After creating the database for this tool, this command is used to initialise the database.
```
invoice -f INVOICE_DB init
```
## DB commands
This command is used to manage invoice database. DB commands have some subcommands to manage. They are listed below:
1. Info : Summarise database status
1. Update : Update the database to the latest version
1. Migrate : Create database migrations (not needed for end users)
```
invoice -f INVOICE_DB db info
```
## Summary Commands
This command is used to show a summary of the database contents. It'll print on the screen.
1. -c/--chronological : Order by date rather than id
1. -v/--verbose : Print detailed summary
1. -d/--dump : Dump the entire database in a format that can be imported
```
invoice -f INVOICE_DB summary -v
```
## Account
In the account section, we can add multiple accounts, like multiple companies. To manage account section we can use some subcommands like:

* Add:
This operation is used to create a new account. We can use command line arguments like :
   1. -n/--name : Name of Account
   1. -s/--signatory : Name of Signatory
   1. -a/--address : Billing address account
   1. -p/--phone : Phone Number
   1. -e/--email : Email Address
   1. --pan : PAN number
   1. --serve : Service Tax number
   1. --bank-details :  Bank details. Must include bank name, address, account number, account holders name, IFSC code and any other details.
   1. --prefix : Invoice number prefix
```
invoice -f INVOICE_DB account add -n name -s sign -a addr -p 76543 -e email --bank-details 'HDFC Bank,calicut'
```
* Edit:
This operation used to edit an existing account. We can select one account by its name. We can use command line arguments like:
   1. -s/--signatory : Name of Signatory
   1. -a/--address : Billing address account
   1. -p/--phone : Phone Number
   1. -e/--email : Email Address
   1. --pan : PAN number
   1. --serve : Service Tax number
   1. --bank-details :  Bank details. Must include bank name, address, account number, account holders name, IFSC code and any other details.
   1. --prefix : Invoice number prefix
```
invoice -f INVOICE_DB account edit name --pan 7654egh
```
* Show:	
This operation used to show the account with the name. 
```
invoice -f INVOICE_DB account show name
```
* List: 	
This operation used to list accounts.
```
invoice -f INVOICE_DB account ls
```
## Client
In the client section, we can add clients are under the corresponding accounts. To manage client section we can use some subcommands like. 
* Add:
This operation used to add a new client. We use some command line arguments like:
   1. -n/--name : Name of client
   1. -a/--account : Name of account under which this client is to be registered
   1. -b/--bunit : Units to bill in (e.g. INR)
   1. --address : Client billing address
   1. -p/--period: Day of month on which this customer should be billed.
   1. invoice -f invoice.db client add  -n NAME -a ACCOUNT -b INR --address ADDRESS -p period
* List:
This operation is used to list all clients
```
invoice -f INVOICE_DB client ls
```
* Edit:	
This operation used to edit an existing client. We can select one client by its name. We can use command line arguments like:
   1. -a/--account : Name of account under which this client is to be registered
   1. -b/--bunit : Units to bill in (e.g. INR)
   1. --address : Client billing address
   1. -p/--period: Day of month on which this customer should be billed.
```
invoice -f INVOICE_DB client edit  NAME -a name -b BChange --address 'first floor, B building' --period period
```
* Show:	
This operation used to show details of a client with the name.
```
invoice -f INVOICE_DB client show  NAME
```
## Template
The template is used to generate invoice and timesheet with proper letterhead template. Here listed some subcommands to manipulate templates.
* Add:
This command is used to add a new template. We can use some command line arguments like.
   1. -n/--name : Name of Template 
   1. -d/--desc : Description of template
   1. -l/--letterhead : Add a letterhead to use as a base PDF
``` 
invoice -f INVOICE_DB template add -n samplename
```
* Edit:
This command is used to edit the existing template with the name. We can use some arguments like::
   1. -d/--desc : change description of template
   1. -l/--letterhead : Change template letterhead to this file
``` 
invoice -f INVOICE_DB template edit templatename -l ~/Documents/invoice_t1.pdf 
```
* Remove:
This command is used to delete template with the name.
```
invoice -f INVOICE_DB template rm samplename
```
* List:
This command is used list all templates.
``` 
invoice -f INVOICE_DB template ls
```
## TimeSheet
In this section, the system is managing the timesheet of the employee, the time they worked for the client. Here listed some subcommands to manipulate timesheet.
* Show:
This command is used to display timesheet details with id 
```
invoice -f INVOICE_DB timesheet show 3
```
* Remove:
This command is used to delete an existing timesheet with id
```
invoice -f INVOICE_DB timesheet rm 1
```
* Edit:
This command is used to edit an existing timesheet with id. We can use some arguments like:
   1. -d/--date : Change timesheet date (e.g. 10/Aug/2010)
   1. -e/--employee : Change employee name
   1. -c/--client : Change timesheet client
   1. -s/--description : Change timesheet description
``` 
invoice -f INVOICE_DB timesheet edit 2 -e Ligin -c NAME -s DESCRIPTION  -d 04/Oct/2018
```
* Add:		
This command is used to manually add a timesheet. i.e. write it out fully in a text buffer. This is not something that's commonly used. It makes more sense to use timesheet import. Some command line arguments are listed below.
   1. -d/--date : Timesheet date (e.g. 10/Aug/2010)
   1. -e/--employee : Employee name
   1. -c/--client : Client name
   1. -s/--description : Description of timesheet
   1. -t/--template :  Template to use
* List:
This command is used to list timesheets
```
invoice -f INVOICE_DB timesheet ls
```
* Import:
This command is used to import new timesheet. We can use some command line arguments like.
   1. -d/--date : timesheet date (10/Aug/2010)
   1. -e/--employee : employee name 
   1. -c/--client : client name
   1. -t/--template : Template to use timesheet : timesheet file instead of timesheet 

```
invoice -f INVOICE_DB timesheet import -e Hasna -c IRF -s Imported -t sample -d 02/Oct/2018 ../../work.org 
```
* Parse:
This command is used to parse and print a timesheet. And the given timesheet to see if there are any errors and it looks good.

```
invoice -f INVOICE_DB timesheet parse ../../work.org
```
* Generate : 
This operation will take a timesheet that's already imported and then create a PDF or text version of it which can be sent to the client. Here we can use some command line arguments like: 
   1. -d/--id : generate timesheet with this id (override other options)
   1. f/--from : generate all invoices since this date (10/Aug/2010). 
   1. -t/--to : generate all invoices till this date (10/Aug/2010).
   1. --format : Format to output timesheet.
   1. -e/--employee : generate timesheets only for this employee
   1. -c/--client : which client to generate invoices for.
   1. -w /--overwrite : overwrite existing generated files.


## Invoice
In this section, the system is managing the Invoices. Here listed some subcommands to manage invoice.
* Show:	
This command is used to display invoice details with id.	
```invoice -f INVOICE_DB invoice show 5
```
* List:
This command is used to list the invoices and we can use different types of filtering by adding command line arguments. They are listed below:
   1. --from : show only invoices since this date (10/Aug/2010). Use 'a’ to list from the beginning.
   1. --to : show only invoices till this date (10/Aug/2010). 
   1. -c /--client : show only invoices for this client
   1. -g/--tag : show only invoices with this tags. Can be given multiple times.
   1. -a/--all : show all invoices (including cancelled)

```invoice -f INVOICE_DB invoice ls
```
* Add:
Invoice add will open an editor with a buffer where you can add an invoice. You can type the fields into the table that gets displayed and create a new invoice. e.g. if you use a template that has 3 fields (S.no, description, and amount), you will get something like
 | | | |

You can then edit it to be like this

| 1 | Senior engineer| 1000|
|2  | Junior engineer| 500|

and save it to create an invoice.
```
invoice -f INVOICE_DB invoice add -c IRF -t sample -p PARTICULARS
```
* Remove:
This command used to delete an invoice with id
```invoice -f INVOICE_DB invoice rm 1
```
* Edit: 
This command used to edit an existing invoice with id

```invoice -f INVOICE_DB invoice edit 2 -c NAME
```
* Generate:
this command is used to generate an invoice. Here we can use some command line arguments.
   1. -i/--id : generate invoice with this if
   1. -f/--from : generate all invoices since this date (10/Aug/2010). 
   1. -t/--to : generate all invoices till this date (10/Aug/2010).
   1. --format : Format to output invoice
   1. -c/--client : which client to generate invoices for. 
   1. -w /--overwrite : overwrite existing generated files.

## Tag
It's to give labels to invoices like (paid, unpaid, cancelled etc.).when we list invoices. We can filter by tags. Here listed some subcommands to manage tag.
* Add :
This command is used to create a new tag. And the command line argument is given below:
   1. Name : Name of new tag to add
```
invoice -f INVOICE_DB tag add tag_name
```
* Remove :
This command is used to delete an existing tag with the name.
```
invoice -f INVOICE_DB tag rm tag_name
```
* List: 
This command is used to list all the tags.
```
invoice -f INVOICE_DB tag ls
```
