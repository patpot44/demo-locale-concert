# Blue Bank

Sample HTTP-based web app that simulates a bank's payment processing network, allowing users to create artificial bank accounts and complete transactions.

This is a modified fork of Google's Bank of Anthos application.

**Bank of Anthos** is a sample HTTP-based web app that simulates a bank's payment processing network, allowing users to create artificial bank accounts and complete transactions.

## Screenshots

| Sign in                                                                                                        | Home                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| [![Login](/docs/img/login.png)](/docs/img/login.png) | [![User Transactions](/docs/img/transactions.png)](/docs/img/transactions.png) |


## Service architecture

![Architecture Diagram](/docs/img/architecture.png)

| Service                                                 | Language      | Description                                                                                                                                  |
| ------------------------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| [frontend](/src/frontend)                              | Python        | Exposes an HTTP server to serve the website. Contains login page, signup page, and home page.                                                |
| [ledger-writer](/src/ledger/ledgerwriter)              | Java          | Accepts and validates incoming transactions before writing them to the ledger.                                                               |
| [balance-reader](/src/ledger/balancereader)            | Java          | Provides efficient readable cache of user balances, as read from `ledger-db`.                                                                |
| [transaction-history](/src/ledger/transactionhistory)  | Java          | Provides efficient readable cache of past transactions, as read from `ledger-db`.                                                            |
| [ledger-db](/src/ledger/ledger-db)                     | PostgreSQL    | Ledger of all transactions. Option to pre-populate with transactions for demo users.                                                         |
| [user-service](/src/accounts/userservice)              | Python        | Manages user accounts and authentication. Signs JWTs used for authentication by other services.                                              |
| [contacts](/src/accounts/contacts)                     | Python        | Stores list of other accounts associated with a user. Used for drop down in "Send Payment" and "Deposit" forms.                              |
| [accounts-db](/src/accounts/accounts-db)               | PostgreSQL    | Database for user accounts and associated data. Option to pre-populate with demo users.                                                      |
| [loadgenerator](/src/loadgenerator)                    | Python/Locust | Continuously sends requests imitating users to the frontend. Periodically creates new accounts and simulates transactions between them.      |


