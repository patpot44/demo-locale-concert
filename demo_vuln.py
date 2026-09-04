# demo_vuln.py — Application de démonstration IBM Concert Secure Coder
# Simule le code source de techcorp-erp v3.4.1 (module auth/db)
# Contient plusieurs vulnérabilités SAST intentionnelles pour la démo

import sqlite3
import subprocess
import hashlib
import os
import pickle
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────────
# VULN 1 — SQL Injection (CWE-89)
# Sévérité : CRITICAL | CVE-2024-25600
# ─────────────────────────────────────────────
def get_user(username):
    conn = sqlite3.connect("users.db")
    query = "SELECT * FROM users WHERE name = '" + username + "'"  # SAST: SQL Injection
    return conn.execute(query)


# ─────────────────────────────────────────────
# VULN 2 — Command Injection (CWE-78)
# Sévérité : CRITICAL | CVE-2024-21626
# ─────────────────────────────────────────────
def run_report(report_name):
    os.system("generate_report.sh " + report_name)  # SAST: Command Injection


# ─────────────────────────────────────────────
# VULN 3 — Mot de passe en dur (CWE-798)
# Sévérité : HIGH
# ─────────────────────────────────────────────
DB_PASSWORD = "S3cr3t!ERP2024"  # SAST: Hardcoded credential
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.hardcoded"  # SAST: Hardcoded secret


# ─────────────────────────────────────────────
# VULN 4 — Hachage faible MD5 (CWE-327)
# Sévérité : HIGH | CVE-2024-3094
# ─────────────────────────────────────────────
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()  # SAST: Weak cryptographic hash (MD5)


# ─────────────────────────────────────────────
# VULN 5 — Désérialisation non sécurisée (CWE-502)
# Sévérité : CRITICAL | CVE-2024-38819
# ─────────────────────────────────────────────
def load_session(session_data):
    return pickle.loads(session_data)  # SAST: Insecure deserialization


# ─────────────────────────────────────────────
# VULN 6 — XXE — XML External Entity (CWE-611)
# Sévérité : HIGH
# ─────────────────────────────────────────────
def parse_config(xml_input):
    tree = ET.fromstring(xml_input)  # SAST: XXE — XML parsed without disabling external entities
    return tree


# ─────────────────────────────────────────────
# VULN 7 — Path Traversal (CWE-22)
# Sévérité : HIGH | CVE-2024-27198
# ─────────────────────────────────────────────
def read_log(filename):
    base_dir = "/var/log/erp/"
    path = base_dir + filename  # SAST: Path traversal — no sanitization
    with open(path, "r") as f:
        return f.read()


# ─────────────────────────────────────────────
# VULN 8 — Shell injection via subprocess (CWE-78)
# Sévérité : CRITICAL
# ─────────────────────────────────────────────
def backup_db(db_name):
    subprocess.call("pg_dump " + db_name + " > /backup/dump.sql", shell=True)  # SAST: Shell injection
