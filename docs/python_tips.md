=======================================
print(f"", end="")
The end="" parameter in the print() function controls what is printed at the end of the line. By default, print() ends with a newline character (\n), so each print() call outputs on a new line.

By setting end="", you're telling Python not to add a newline after printing. Instead, it will just stay on the same line, allowing the next output (in this case, ✅ (Account: {account_id}) or the error message) to appear on the same line.
=======================================
BotoCoreError and ClientError
These are exception classes from the AWS SDK for Python (boto3 and its lower-level library botocore).
    1. BotoCoreError: Base class for all low-level errors from botocore. 
    2. ClientError:Raised when AWS returns an error response, like:
        Invalid credentials
        Missing permissions
        Invalid input to an API call
=======================================
sys.exit(1)
This immediately stops the Python script and exits with a status code of 1, which typically means "error".
    sys.exit(0) → success
    sys.exit(1) (or any non-zero number) → failure
By calling sys.exit(1) after printing the error, the script:
    Aborts execution
    Signals to the environment (e.g., CI/CD, shell script) that something went wrong
=======================================
