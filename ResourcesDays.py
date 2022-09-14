"""
Purpose

Download the last 14 days Resources Report from AWS Cost Explorer Service.
"""

import boto3
import datetime
import pandas as pd
import os
import argparse

access_key = os.environ.get("ACCESS_KEY")
secret_key = os.environ.get("SECRET_KEY")


def epoch_time_convert(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time / 1000)


def parser_args():
    # Get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14, help="Provide days!")
    parser.add_argument('--akey', type=str, default=access_key, help="Access key needed!")
    parser.add_argument('--skey', type=str, default=secret_key, help="Secret key needed")

    args = parser.parse_args()
    return args


def check_params(args):
    # Check if token is given
    if "days" in args:
        r_days = args.days
    else:
        raise ValueError('Provide days as an argument --days')

    if "akey" in args and "skey" in args:
        a_key = args.akey
        s_key = args.skey
    else:
        raise ValueError('Access key and Secret key must be supplied as an argument --akey --skey')
    return r_days, a_key, s_key


def api_call():
    cd = boto3.client('ce', region_name='us-east-1',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)

    now = datetime.datetime.utcnow()
    print('Today: ', now)

    start = (now - datetime.timedelta(days=current_args.days)).strftime('%Y-%m-%d')
    print('Start Date: ', start)
    end = now.strftime('%Y-%m-%d')
    print('End Date: ', end)

    # GetCostAndUsageWithResources
    data = cd.get_cost_and_usage_with_resources(TimePeriod={'Start': start, 'End': end},
                                                Granularity='DAILY', Metrics=['UnblendedCost'],
                                                Filter={'Dimensions':
                                                            {'Key': 'SERVICE',
                                                             'Values': ['Amazon Elastic Compute Cloud - Compute']}},
                                                GroupBy=[{'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}])
    return data, now, start, end


def read_data(data):
    list_of_data = data['ResultsByTime']
    amounts = []
    dates = []
    resources = []
    dic = {}
    for i in list_of_data:
        for group in i['Groups']:
            resources.append(group['Keys'][0])
            print('Group keys')
            print(group['Keys'][0])
            amounts.append(group['Metrics']['UnblendedCost']['Amount'])
            dates.append(datetime.datetime.strptime(i['TimePeriod']['Start'][:10], '%Y-%m-%d'))

        dic = {'Date': dates, 'Resource': resources, 'Amount': amounts}
    return dic


def write_xls_pd(dic, now):
    file_path = 'c:\\Users\\ekoutsoff\\Desktop\\AWS\\Costs\\pyCosts\\' + 'ResourcesCosts ' + str(
        now.strftime('%Y-%m-%d')) + '.xlsx'

    df = pd.DataFrame.from_dict(dic)

    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    df.to_excel(writer, index=False)

    writer.save()

    return file_path


current_args = parser_args()
report_days, aws_access_key, aws_secret_key = check_params(current_args)
report_data, date_now, date_start, date_end = api_call()
data_dict = read_data(report_data)
path_of_file = write_xls_pd(data_dict, date_now)
print()
print(path_of_file)
print()
