"""
Concert National Bank - Transaction-heavy load generator
Designed to stress the Kafka/Redis/Postgres pipeline
"""

import json
import logging
import time
from string import ascii_letters, digits
from random import randint, random, choice

from locust import HttpUser, TaskSet, task, between

MASTER_PASSWORD = "password"
TRANSACTION_ACCT_LIST = [str(randint(1111100000, 1111199999)) for _ in range(50)]

def generate_username():
    return ''.join(choice(ascii_letters + digits) for _ in range(15))

class TransactionHeavyTasks(TaskSet):
    """
    Authenticated tasks focused on transactions.
    Signup once, then hammer payments and deposits.
    """

    def on_start(self):
        """Create account, login, seed with large balance"""
        self.authenticated = False
        self.username = generate_username()

        while not self.authenticated:
            self.username = generate_username()
            userdata = {
                "username": self.username,
                "password": MASTER_PASSWORD,
                "password-repeat": MASTER_PASSWORD,
                "firstname": self.username,
                "lastname": "LoadTest",
                "birthday": "01/01/2000",
                "timezone": "82",
                "address": "1021 Valley St",
                "city": "Seattle",
                "state": "WA",
                "zip": "98103",
                "ssn": "111-22-3333"
            }
            with self.client.post("/signup", data=userdata, catch_response=True) as response:
                for r_hist in response.history:
                    if r_hist.cookies.get('token') is not None:
                        response.success()
                        self.authenticated = True
                        # Seed large balance
                        self.deposit_amount(10000000)
                        return
                response.failure("signup failed")
            # Back off before retrying
            time.sleep(1 + random() * 2)

    def deposit_amount(self, amount):
        """Deposit a specific amount"""
        acct_info = {
            "account_num": choice(TRANSACTION_ACCT_LIST),
            "routing_num": "111111111"
        }
        transaction = {
            "account": json.dumps(acct_info),
            "amount": amount,
            "uuid": generate_username()
        }
        self.client.post("/deposit", data=transaction, name="/deposit [seed]")

    @task(10)
    def payment(self):
        """Send payment - hits ledgerwriter -> Kafka -> transaction-processor"""
        transaction = {
            "account_num": choice(TRANSACTION_ACCT_LIST),
            "amount": round(random() * 10, 2),
            "uuid": generate_username()
        }
        with self.client.post("/payment", data=transaction, catch_response=True) as response:
            if response.url and "failed" in response.url:
                response.failure("payment failed")

    @task(10)
    def deposit(self):
        """Deposit - also hits ledgerwriter -> Kafka -> transaction-processor"""
        acct_info = {
            "account_num": choice(TRANSACTION_ACCT_LIST),
            "routing_num": "111111111"
        }
        transaction = {
            "account": json.dumps(acct_info),
            "amount": round(random() * 100, 2),
            "uuid": generate_username()
        }
        with self.client.post("/deposit", data=transaction, catch_response=True) as response:
            if response.url and "failed" in response.url:
                response.failure("deposit failed")

    @task(3)
    def view_home(self):
        """View home - hits balancereader (Redis) + transactionhistory (Redis)"""
        self.client.get("/home")

    @task(1)
    def view_index(self):
        """View landing page"""
        self.client.get("/")


class TransactionUser(HttpUser):
    """
    User that signs up once then hammers transactions.
    80% of tasks are payments/deposits (Kafka pipeline).
    """
    tasks = [TransactionHeavyTasks]
    wait_time = between(0.5, 1.0)
