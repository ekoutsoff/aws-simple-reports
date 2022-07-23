import boto3
from boto3 import client
import datetime
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import xlsxwriter
import os
import argparse


def ctime_convert(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time/1000)

def parserargs():
    # Get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="Provide days!")
    parser.add_argument('--akey', type=str, default="", help="Access key needed!")
    parser.add_argument('--skey', type=str, default="", help="Secret key needed")

    args = parser.parse_args()
    return args

def check_params(args):
    # Check if token is given
    if "days" in args:
        d_days = args.days
    else:
        raise ValueError('Provide days as an argument --days')

    if "akey" in args and "skey" in args:
        access_key = args.akey
        secret_key = args.skey
    else:
        raise ValueError('Access key and Secret key must be supplied as an argument --akey --skey')
    return d_days, access_key, secret_key

def api_call():

    cd = boto3.client('ce', region_name='us-east-1',
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)

    now = datetime.datetime.utcnow()
    print('Today: ', now)

    start = (now - datetime.timedelta(days=args.days)).strftime('%Y-%m-%d')
    print('Start Date: ', start)
    end = now.strftime('%Y-%m-%d')
    print('End Date: ', end)
    #x = input("wait")

    #GetCostAndUsageWithResources

    data = cd.get_cost_and_usage_with_resources(TimePeriod={'Start': start, 'End': end},
                                Granularity='DAILY', Metrics=['UnblendedCost'],
                                Filter={'Dimensions': {'Key':'SERVICE', 'Values':['Amazon Elastic Compute Cloud - Compute']} },
                                GroupBy=[{'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}])
    return data, now, start, end

def read_data():
    ls = data['ResultsByTime']

    amountLs = []
    act = []
    dateLs = []
    resources = []
    for i in ls:

        for group in i['Groups']:
            resources.append(group['Keys'][0])
            print('Group keys')
            print(group['Keys'][0])
            amountLs.append(group['Metrics']['UnblendedCost']['Amount'])
            dateLs.append(datetime.datetime.strptime(i['TimePeriod']['Start'][:10], '%Y-%m-%d'))

        dic = {'Date': dateLs, 'Resource': resources, 'Amount': amountLs}
    return dic

def write_xls_pd(dic):
    strFile = 'c:\\Users\\ekoutsoff\\Desktop\\AWS\\Costs\\pyCosts\\' + 'ResourcesCosts ' + str(
        now.strftime('%Y-%m-%d')) + '.xlsx'

    df = pd.DataFrame.from_dict(dic)

    writer = pd.ExcelWriter(strFile, engine='xlsxwriter')

    df.to_excel(writer, index=False)

    writer.save()

    print(strFile)


args = parserargs()
d_days, access_key, secret_key = check_params(args)
data, now, start, end = api_call()
dic = read_data()
write_xls_pd(dic)



