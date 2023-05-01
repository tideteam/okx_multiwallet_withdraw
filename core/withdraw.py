# 載入設定
import json
config_filepath = 'config.json'
address_filepath = 'wallets.txt'
with open(config_filepath) as f:
    config_dict = json.load(f)

with open(address_filepath) as f:
    address_list = f.read().split()
    
import okex.Funding_api as Funding
import pandas as pd
import requests
import time
import hashlib
import hmac
import base64
import random
import datetime


def get_time():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"

def signature_in(timestamp, method, request_path, body, secret_key):
    if str(body) == '{}' or str(body) == 'None':
        body = ''
    else:
        body = json.dumps(body)
    message = str(timestamp) + str.upper(method) + request_path + str(body)
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    output = mac.digest()
    return base64.b64encode(output)

def coin_withdraw(ccy, amt, dest, toAddr, pwd, fee):
    url = "https://www.okex.com/api/v5/asset/withdrawal"

    timestamp = get_time()

    params = {
        "amt" : amt,
        "fee" : fee,
        "dest" : dest,
        "ccy" : ccy,
        "chain": config_dict['network'],
        "toAddr": toAddr,
    }

    signature = signature_in(timestamp, 'POST', '/api/v5/asset/withdrawal', params, config_dict['secret'])

    headers = {
        "OK-ACCESS-KEY": config_dict['key'],
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": config_dict['passphrase'],
        "Content-Type": "application/json"
    }

    # 發送請求
    response = requests.post(url, headers=headers, data=json.dumps(params))
    # 解析回應
    result = response.json()

    if response.status_code == 200:
        result = f"提款成功"
    else:
        result = f"提款失敗：{result}"
    return result



fundingAPI = Funding.FundingAPI(config_dict['key'], config_dict['secret'], config_dict['passphrase'],False,flag='0')
df_coin = pd.DataFrame(fundingAPI.get_currency()['data'])
minfee = float(df_coin.loc[(df_coin['ccy']==config_dict['token'])&(df_coin['chain']==config_dict['network']),'minFee'])

# 檢查餘額

df_bal = pd.DataFrame(fundingAPI.get_balances()['data'])
df_bal['availBal'] = df_bal['availBal'].astype(float)
bal = float(df_bal.loc[df_bal['ccy']==config_dict['token'],'availBal'])

print(f"餘額: {bal} {config_dict['token']}")



if bal>=(len(address_list)*(float(config_dict['amount']['min'])+minfee)):
    for address in address_list:
        randomAmt = round(random.uniform(config_dict['amount']['min'],config_dict['amount']['max']),2)
        withdraw=coin_withdraw(ccy=config_dict['token'], amt=randomAmt, dest="4", toAddr=address, pwd="pwd", fee=minfee)
        
        print(f"送出提幣需求: {randomAmt} {config_dict['network']} - {address}")
        print(withdraw)
        delay = random.randint(config_dict['delay']['min'],config_dict['delay']['max'])
        for t in range(delay):
            print(f'waiting - {delay-t}s', end="\r")
            time.sleep(1)        

    df_bal = pd.DataFrame(fundingAPI.get_balances()['data'])
    df_bal['availBal'] = df_bal['availBal'].astype(float)
    bal = float(df_bal.loc[df_bal['ccy']==config_dict['token'],'availBal'])
    print(f"剩下餘額: {bal} {config_dict['token']}")

else:
    print(f"餘額不足: {bal-(len(address_list)*(config_dict['amount']+minfee))}")