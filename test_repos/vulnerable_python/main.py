# Vulnerable Python Sample Application (For DevSecOps Security Gate Testing)
import os

AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"  # HARDCODED SECRET - CRITICAL
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # HARDCODED SECRET - CRITICAL

def execute_user_code(user_input):
    # DANGEROUS EVAL CALL - CRITICAL
    return eval(user_input)

def run_command(cmd_str):
    # DANGEROUS SYSTEM COMMAND - HIGH
    os.system(cmd_str)

if __name__ == "__main__":
    print("Vulnerable app ready")
