# Introduction
This tool categorizes credit card transactions into user defined "buckets" and
stores the results in a Google spreadsheet.

## Overview
This tool is narrowly constructed to parse QFX or OFX files that contain credit
card transactions (e.g. `<ACCTTYPE>CREDITLINE`), categorize them, and then store
the results in a Google spreadsheet for further analysis.

### Features
* User defined categories (See: `--alloc-columns`).
* A single transaction can be split across multiple categories.
* Statement periods are isolated into separate worksheets (See: `--statement-date`).
* Transactions that were previously classified within a statement period are skipped.

## Setup
Setup guidance is geared towards macOS and Linux users. I have no idea how this
sort of thing works in Windows; documentation patches gratefully accepted.

Aside from cloning this repo (or just copying the script directly), setup
splits along three lines - configuration, Python3 stuff, and Google stuff.

### Configuration
An optional configuration file can be generated to manage information that would
otherwise have to be supplied via command line arguments.

The default configuration file location is `~/.config/cctools/ccct.config.json`.
Alternate locations can be specified with the `--config-file` command line
argument.

* Information found in the configuration file supplements arguments found on the command line.
* Command line arguments take precedence over information supplied by the configuration file.
* Everything but the QFX file and statement date can be supplied via command line or configuration file.

Example config file:
```
{
	"credential_dir": "~/.google",
	"bank_id": 314074269,
	"document_id": "2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg",
	"alloc_columns": [{
		"short": "ap",
		"long": "Amazon Purchases"
	},{
		"short": "pc",
		"long": "Petcare"
	},{
		"short": "af",
		"long": "Auto Fuel"
	}]
}
```

### Bash Helper Functions
The command line can be a bit unwieldy, so a helper function similar to the
following might prove useful. Add it to your `~/.bash_profile` if you want
it available anytime you log in.
```
ccrec() {
    local STMT_DATE=$1

    local PROJ=~/path/to/cctools
    local EXEC=${PROJ}/ccct/ccct
    local QFX="~/path/to/export-${STMT_DATE}.qfx"

    if [[ "${STMT_DATE}" =~ ^(19|20)[0-9]{2}(0[1-9]|1[0-2])26$ ]]; then
        source ${CLONE}/.venv/bin/activate
        ${EXEC} --credential-dir=CHANGEME --fx-file=${QFX} --bank-id=CHANGEME --statement-date=${STMT_DATE} --alloc-columns='CHANGEME' --document-id='CHANGEME'
        deactivate
    else
        echo "Error: Invalid statement date!"
    fi
}
```

If you choose to use a configuration file, this is a version of the same
function with the minimum arguments supplied.
```
ccrec() {
    local STMT_DATE=$1

    local PROJ=~/path/to/cctools
    local EXEC=${PROJ}/ccct/ccct
    local QFX="~/path/to/export-${STMT_DATE}.qfx"

    source ${PROJ}/.venv/bin/activate
    if [[ "${STMT_DATE}" =~ ^(19|20)[0-9]{2}(0[1-9]|1[0-2])26$ ]]; then
        ${EXEC} --fx-file=${QFX} --statement-date=${STMT_DATE}
    else
        echo "Error: Invalid statement date!"
    fi
    deactivate
}
```

### Python3 Stuff
You are going to need the following python3 libraries:
* [`ofxtools`](https://pypi.org/project/ofxtools/)
* [`google-api-python-client`](https://pypi.org/project/google-api-python-client/)
* [`google-auth-httplib2`](https://pypi.org/project/google-auth-httplib2/)
* [`google-auth-oauthlib`](https://pypi.org/project/google-auth-oauthlib/)
* [`jsonschema`](https://pypi.org/project/jsonschema/)

If you use [`pip3`](https://pypi.org/project/pip/), you can install them all at
once in a virtual environment:
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib ofxtools jsonschema
deactivate
```

### Google Stuff
Google does not seem to have a simple "hobbyist" process for programmatically
accessing your own Google Drive content. You have to create a cloud project,
add the Google Sheets API to the project, generate OAuth credentials that are
stored locally in the form of a JSON file, and then add yourself to the project
as a test user.

I found the [Google Sheets Python quickstart](https://developers.google.com/sheets/api/quickstart/python)
to be quite helpful with the above. The following steps are a distilled version.

1. Go to the [Google Cloud Console](https://console.cloud.google.com) and create a new project.
2. Go to [APIs and Services](https://console.cloud.google.com/apis/dashboard) and add the Google Sheets API to your project.
3. Go to the [Credentials](https://console.cloud.google.com/apis/credentials) page and create credentials.
4. Download the credentials to a file called `credentials.json` and store them somewhere accessible. I stored mine in `~/.google`.
5. Add yourself as a test user on the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).

If you did everything correctly, the first time you run `ccct` you will be
redirected to a web page in your default web browser to grant access. This will
generate a `token.json` file that also ends up in `~/.google` (assuming that
is where you chose to store your credentials).

The `token.json` file is periodically updated when `ccct` is run. If you run
into authentication issues, you can delete this file and go through the web page
access grant process again the next time you run `ccct`.

## Operation
Start by reviewing the usage statement: `./ccct --help`.

Here is an example of what the categorization process looks like:
```
$ ./ccct --credential-dir=${HOME}/.google --fx-file=${HOME}/Downloads/export-20231226.qfx --bank-id=XXXXXXXXX --statement-date=20231226 --alloc-columns='ap:pc:af'
Spreadsheet Created: CreditCardTransactions
Spreadsheet ID: 2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg
Found 0 worksheet transactions.
Found 129 OFX transactions.

Classify transaction 1 of 129:
	TID:	1468216B834LQ1QER6
	Date:	2023-12-26T12:00:00+00:00
	Type:	DEBIT
	Amount:	-44.03
	Name:	AMZN Mktp US*XY7AC8WA7   Amzn.co
	Memo:	AMZN Mktp US*XY7AC8WA7   Amzn.com/billWA
Allocate transaction [[ap, pc, af]][44.03]: ap
```

If you use a configuration file to define your allocation columns, you will see
an additional `?` character that displays a map of long names.

```
$ ./ccct --fx-file=${HOME}/Downloads/export-20231226.qfx --statement-date=20231226
Spreadsheet Created: CreditCardTransactions
Spreadsheet ID: 2CZrPH3M-Lg-TmD5luXu7loG3svABgfGP23txXbar7dg
Found 0 worksheet transactions.
Found 129 OFX transactions.

Classify transaction 1 of 129:
	TID:	1468216B834LQ1QER6
	Date:	2023-12-26T12:00:00+00:00
	Type:	DEBIT
	Amount:	-44.03
	Name:	AMZN Mktp US*XY7AC8WA7   Amzn.co
	Memo:	AMZN Mktp US*XY7AC8WA7   Amzn.com/billWA
Allocate transaction [[ap, pc, af, ?]][44.03]: ?
	ap:	Amazon Purchases
	pc:	Petcare
	af:	Auto Fuel
Allocate transaction [[ap, pc, af, ?]][44.03]:
```

### Transaction Types
Credit card transactions come in two flavors, CREDIT and DEBIT. In QFX/OFX
files, transaction CREDIT amounts (refunds and payments) are positive numbers
and transaction DEBIT amounts (charges) are negative numbers.

### Sign Inversion
In order to have a clear picture of what is owed (i.e. what transaction CREDIT
the bank is now expecting) the sign on transaction amounts is inverted during
the categorization process. Most bank websites will display transaction data in
a similar fashion, but rather than display a transaction CREDIT as a negative
number they use standard accounting notation (e.g. `(10.02)`).

You can also think of this in terms of the credit card balance if that makes
more sense. A transaction DEBIT is a CREDIT on the balance. The card's balance
is DEBITed or "paid off" with a CREDIT transaction.

### Transaction Categorization
Transactions can be allocated to one or more categories, however a card
transaction CREDIT can only be allocated as a payment DEBIT, and a card
transaction DEBIT only be allocated as a payment CREDIT. No mixing and matching
is allowed.

Given a transaction DEBIT of -44.03, one might choose to allocate a payment
CREDIT of 20 to category "ap" and a payment CREDIT of 24.03 to category "pc";
both must be positive values representing the sum total of the payment CREDIT
"owed" on the original transaction DEBIT. One cannot allocate a transaction
DEBIT in terms of a payment CREDIT on one category and a payment DEBIT on
another category, even if the total is equal to the original transaction DEBIT.

Here is an example of allocating a transaction DEBIT to a single category:
```
Classify transaction 1 of 129:
	TID:	1468216B834LQ1QER6
	Date:	2023-12-26T12:00:00+00:00
	Type:	DEBIT
	Amount:	-44.03
	Name:	AMZN Mktp US*XY7AC8WA7   Amzn.co
	Memo:	AMZN Mktp US*XY7AC8WA7   Amzn.com/billWA
Allocate transaction [[ap, pc, af, ?]][44.03]: ap
```

Here is an example of allocating a transaction DEBIT to multiple categories:
```
Classify transaction 1 of 129:
	TID:	1468216B834LQ1QER6
	Date:	2023-12-26T12:00:00+00:00
	Type:	DEBIT
	Amount:	-44.03
	Name:	AMZN Mktp US*XY7AC8WA7   Amzn.co
	Memo:	AMZN Mktp US*XY7AC8WA7   Amzn.com/billWA
Allocate transaction [[ap, pc, af, ?]][44.03]: ap 20
Allocate transaction [[ap(20.0), pc, af, ?]][24.03]: pc
```

A category can be deallocated by allocating zero to that category, like this:
```
Classify transaction 1 of 129:
	TID:	1468216B834LQ1QER6
	Date:	2023-12-26T12:00:00+00:00
	Type:	DEBIT
	Amount:	-44.03
	Name:	AMZN Mktp US*XY7AC8WA7   Amzn.co
	Memo:	AMZN Mktp US*XY7AC8WA7   Amzn.com/billWA
Allocate transaction [[ap, pc, af, ?]][44.03]: ap 20
Allocate transaction [[ap(20.0), pc, af, ?]][24.03]: ap 0
Allocate transaction [[ap, pc, af, ?]][44.03]:[44.03]: pc 20
Allocate transaction [[ap, pc(20.0), ?]][24.03]: af
```

A transaction CREDIT allocation works the same way, except one uses negative
rather than positive numbers.

### Spreadsheet Creation
If the `--document-id` argument is omitted and not otherwise included in a
configuration file, a new spreadsheet will be created. If you do not already
have a spreadsheet in mind, this is probably the best place to start.

Subsequent runs should include the document ID either by using the
`--document-id` argument or adding it to your configuration file.

The document ID is output by `ccct` and can also be found embedded in the
spreadsheet URL.

### Statement Worksheets
Endlessly accumulating credit card transactions on a single worksheet will
get unweildy very quickly. The `--statement-date` argument creates a worksheet
with the statement date as the title and saves the current batch of categorized
transactions to it. If the named worksheet already exists, any transactions that
were previously categorized to that worksheet are skipped during the
categorization process.

### User Defined Categories
The `--alloc-columns` argument defines the allocation categories as a colon
delimited string. These category names will appear in the first row of the
statement worksheet and on the command line interface during the categorization
process.

When adding transactions to an existing statement worksheet the allocation
columns must match the existing categories in the statement worksheet header or
`ccct` will exit with an error.

The use of very short category names is advisable in order to simplify the
categorization process. Configuring allocation columns with a configuration file
allows for the addition of a long description string.

## Open Financial Exchange (OFX)
QFX is Quicken's proprietary superset of the OFX specification which is
maintained by the [Financial Data Exchange](https://financialdataexchange.org).
The OFX specification can be found
[here](https://financialdataexchange.org/common/Uploaded%20files/OFX%20files/OFX%20Banking%20Specification%20v2.3.pdf).

## Gotchas
Despite clear guidance to the contrary, some banks have a bad habit of
occasionally reusing OFX transaction identifiers (FITID). To overcome this,
transactions are compared as tuples to determine if a particular transaction can
be skipped as previously categorized. If you determine that your bank is reusing
transaction identifiers it is best to report the issue to one of their technical
contacts. I have had some success reporting this problem to my own bank, so teel
free to reach out if you need help.
