import requests
import re
import json
import os
import boto3
from datetime import datetime 

from bs4 import BeautifulSoup as bs

# 環境変数から取得
SCRAPING_URL = os.environ['scraping_url']
SCRAPING_ID = os.environ['scraping_id']
WORK_TITLE = os.environ['work_title']
WEBHOOK_URL = os.environ['webhook_url']
DISCORD_MENTION_ID = os.environ['discord_mention_id']
DISCORD_MENTION_TARGET = os.environ['discord_mention_target']

# ログ出力関数
def logging(errorLv, lambdaName, errorMsg):
  loggingDateStr=(datetime.now()).strftime('%Y/%m/%d %H:%M:%S')
  print(loggingDateStr + ' ' + lambdaName + ' [' + errorLv + '] ' + errorMsg)
  return

# 以前までのMaxIDを取得
def get_max_id(table):
  query_data = table.get_item(
    Key = {
      'ID': SCRAPING_ID,
      'WorkTitle': WORK_TITLE
    }
  )
  max_id = query_data['Item']['MaxID']

  return max_id

def update_max_id(table, max_id):
  table.update_item(
    Key = {
      'ID': SCRAPING_ID,
      'WorkTitle': WORK_TITLE
    },
    UpdateExpression='set MaxID = :m',
    ExpressionAttributeValues = {
      ':m' : max_id
    }
  )
  return

# サイト固有のElementに対するURL, ID取得処理
def unique_process(soup):
  ids = []
  urls = []

  atag_elems = soup.find_all('a', class_= 'create_time')

  for atag_elem in atag_elems:
    work = atag_elem['href']
    urls.append(work)

    id = re.findall(r'\d+', atag_elem['href'])[0]
    ids.append(id)

  return ids, urls

# Webhook
def do_webhook(new_urls):
  headers = {'Content-Type': 'application/json'}

  for new_url in new_urls:
    if DISCORD_MENTION_TARGET == 'user':
      content = {'content': '<@' + DISCORD_MENTION_ID + '>\n' + new_url}
    elif DISCORD_MENTION_TARGET == 'role':
      content = {'content': '<@&' + DISCORD_MENTION_ID + '>\n' + new_url}
    else:
      content = {'content': new_url}

    requests.post(WEBHOOK_URL, json.dumps(content), headers=headers)

# Lambda起動用ハンドラー
def lambda_handler(event, context):
  try:
    logging('info', context.function_name, 'process start')
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('scrapings')

    response = requests.get(SCRAPING_URL)
    soup = bs(response.content, 'html.parser')

    previous_max_id = get_max_id(table) 

    ids, urls = unique_process(soup)

    # 現在のMaxID
    now_max_id = max(ids)

    #IDに違いがない場合
    if previous_max_id == now_max_id:
      logging('success', context.function_name, 'no changes')
      return {
        'statusCode': 200,
        'body': 'not update'  
      }
    
    #MaxIDをdynamoDBに登録
    update_max_id(table, now_max_id)

    # 以前までのMaxIDより新しいURL
    new_urls = [urls[i] for i, x in enumerate(ids) if x > previous_max_id]
    new_urls.reverse()

    do_webhook(new_urls)
  
    logging('success', context.function_name, 'hooked')
    return {
      'statusCode': 200,
      'body': 'hooked'  
    }
    
  except Exception as error :
    logging('error', context.function_name, error)
    return {
      'statusCode': 500,
      'body': type(error) + ': ' + error
    }
