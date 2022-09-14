"""
Purpose

Download the Credentials Report from AWS Identity and Access Management (IAM) accounts.
"""
import os
import datetime
import argparse
import sys
import boto3
import json
import csv
import logging

import time

import pandas as pd
from botocore.exceptions import ClientError

access_key = os.environ.get("ACCESS_KEY")
secret_key = os.environ.get("SECRET_KEY")
logger = logging.getLogger(__name__)


def parser_args():
    # Get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--akey', type=str, default=access_key, help="Access key needed!")
    parser.add_argument('--skey', type=str, default=secret_key, help="Secret key needed")

    args = parser.parse_args()
    return args


def check_params(args):
    # Check if token is given

    if "akey" in args and "skey" in args:
        access_key = args.akey
        secret_key = args.skey
    else:
        raise ValueError('Access key and Secret key must be supplied as an argument --akey --skey')

    if access_key and secret_key:
        return access_key, secret_key
    return access_key, secret_key


def api_call():
    # Access IAM AWS Service
    iam = boto3.client('iam',
                       aws_access_key_id=access_key,
                       aws_secret_access_key=secret_key)
    return iam


def date_element():
    now = datetime.datetime.utcnow()

    idate = now.strftime('%Y-%m-%d')
    fdate = now.strftime("%d%B%Y")

    print('iDate: ', idate)
    print('fDate: ', fdate)
    return idate, fdate


def list_aliases(iam):
    """
    Gets the list of aliases for the current account. An account has at most one alias.

    :return: The list of aliases for the account.
    """
    try:
        response = iam.list_account_aliases()
        aliases = response.get('AccountAliases', [])

        if len(aliases) > 0:
            logger.info("Got aliases for your account: %s.", ','.join(aliases))
        else:
            logger.info("Got no aliases for your account.")
    except ClientError:
        logger.exception("Couldn't list aliases for your account.")
        raise
    else:
        print()
        print("-----------------------------ALIAS-----------------------------")
        print(aliases[0])
        print()
        print(f"Your account alias is             {(aliases[0])} ")
        print()


def get_summary(iam):
    """
    Gets a summary of account usage.

    :return: The summary of account usage.
    """
    try:
        summary = iam.get_account_summary()
        logger.debug(summary["SummaryMap"])
    except ClientError:
        logger.exception("Couldn't get a summary for your account.")
        raise
    else:
        return summary["SummaryMap"]


def generate_credential_report(iam):
    """
    Begin the generation of a credentials report for the current account.
    After that call the get_credential_report to get the latest report.
    A new report can be generated at least four hours after the the last one was generated.
    """
    try:
        response = iam.generate_credential_report()
        logger.info("Generating credentials report for your account. "
                    "Current state is %s.", response['State'])
    except ClientError:
        logger.exception("Couldn't generate a credentials report for your account.")
        raise
    else:
        return response


def get_credential_report(iam):
    """
    Get the recently generated credentials report.

    :return: The credentials report.
    """
    try:
        response = iam.get_credential_report()
        logger.debug(response['Content'])
    except ClientError:
        logger.exception("Couldn't get credentials report.")
        raise
    else:
        return response


def save_credentials_report(dict_resp, idate, new_path):
    # Convert the dict of containing the credentials report to a string
    # Convert the first line to and remove it from the list
    str_resp = dict_resp["Content"].decode('utf-8').split("\n")
    str_headers = map(str, (str_resp.pop(0)).rstrip(',').split(','))
    list_headers = list(str_headers)  # keys of the new dict

    new_dict = {}
    list_dict_records = []

    # Convert the sequence of strings seperated by comma to a list
    # Convert the list to a dict with keys from list_headers and values from the list
    # Append the list with the dict
    for each_string in str_resp:
        list_elements = each_string.split(",")
        # method 1
        # conversion of lists to dictionary
        # using dictionary comprehension
        # dict_record = {list_headers[i]: list_elements[i] for i in range(len(list_headers))}

        # method 2
        # conversion of lists to dictionary
        # using zip()
        dict_record = dict(zip(list_headers, list_elements))

        list_dict_records.append(dict_record)

    # Set the file name
    # open the file for writting
    # Convert the dictionary to CSV with header by using the dictwriter() method of CSV module
    file_name = new_path + "IAM-" + idate + ".csv"
    with open(file_name, 'w', newline="\n") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list_headers)
        writer.writeheader()
        writer.writerows(list_dict_records)

    # Convert the CSV file to XLSX file using Panda
    # Read csv with read_csv() into a Dataframe
    df = pd.read_csv(file_name)
    file_name = new_path + "IAM-" + idate + ".xlsx"
    # Convert the Dataframe to_excel()
    df.to_excel(file_name, sheet_name="IAM", index=False)


def save_pwd_policy(iam, idate, new_path):
    pwd_policy = print_password_policy(iam)
    print()
    print("-------------------------PASSWORD POLICY-------------------------")
    print(pwd_policy)

    file_name = new_path + "PasswordPolicy-" + idate + ".txt"
    with open(file_name, "w") as f:
        f.write(str(pwd_policy))


def save_summary(iam, idate, new_path):
    summary = get_summary(iam)
    print()
    print("-----------------------------SUMMARY-----------------------------")
    print(json.dumps(summary, default=str, indent=2))
    file_name = new_path + "Summary-" + idate + ".txt"
    with open(file_name, "w") as f:
        f.write(json.dumps(summary, default=str, indent=2))


def define_directory(fdate):
    # Directory
    directory = "AWS Reports " + fdate + "\\"

    # Parent Directory path
    parent_directory = "c:\\Users\\ekoutsoff\\Documents\\myWork\\AWS\\Monthly\\Reports\\"
    # Path
    new_path = os.path.join(parent_directory, directory)

    # Create the directory
    ## If folder doesn't exists, create it ##
    if not os.path.isdir(new_path):
        os.mkdir(new_path)
    else:
        print("Folder  " + directory.upper() + "  already exist!")

        x = input("Continue?")
        if x == "y" or x == "Y":
            return new_path
        else:
            sys.exit(0)


def print_password_policy(iam):
    """
    Prints the password policy for the account.
    """
    try:
        pw_policy = iam.get_account_password_policy()
        print("Current account password policy:")
        print(f"\tallow_users_to_change_password: {pw_policy.allow_users_to_change_password}")
        print(f"\texpire_passwords: {pw_policy.expire_passwords}")
        print(f"\thard_expiry: {pw_policy.hard_expiry}")
        print(f"\tmax_password_age: {pw_policy.max_password_age}")
        print(f"\tminimum_password_length: {pw_policy.minimum_password_length}")
        print(f"\tpassword_reuse_prevention: {pw_policy.password_reuse_prevention}")
        print(f"\trequire_lowercase_characters: {pw_policy.require_lowercase_characters}")
        print(f"\trequire_numbers: {pw_policy.require_numbers}")
        print(f"\trequire_symbols: {pw_policy.require_symbols}")
        print(f"\trequire_uppercase_characters: {pw_policy.require_uppercase_characters}")
        printed = True
    except ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchEntity':
            print("The account does not have a password policy set.")
        else:
            logger.exception("Couldn't get account password policy.")
            raise
    else:
        return printed


if __name__ == "__main__":
    args = parser_args()
    access_key, secret_key = check_params(args)

    iam = api_call()
    # dict of all users
    # users = iam.list_users()
    idate, fdate = date_element()

    new_path = define_directory(fdate)

    report_state = None
    while report_state != 'COMPLETE':
        cred_report_response = generate_credential_report(iam)
        old_report_state = report_state
        report_state = cred_report_response['State']
        if report_state != old_report_state:
            print("Credentials Report generation:         ", report_state, sep='')
        else:
            print('.', sep='')
        # stdout.flush() forces it to “flush” the buffer, meaning that
        # it will write everything in the buffer to the terminal,
        # even if normally it would wait before doing so.
        sys.stdout.flush()
        # time method sleep() suspends execution for the given number of seconds. here 1 second
        time.sleep(1)
    print()

    dict_resp = get_credential_report(iam)
    save_credentials_report(dict_resp, idate, new_path)

    list_aliases(iam)
    save_summary(iam, idate, new_path)
    save_pwd_policy(iam, idate, new_path)
