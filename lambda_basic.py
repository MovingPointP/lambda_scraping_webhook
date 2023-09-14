import requests
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

# サイト固有のElementに対するID, Work, URL取得処理
def unique_process(soup):
  ids = []
  works = []
  urls = []

  section_elems = soup.find_all('section')

  for section_elem in section_elems:
    id = section_elem['data-uuid']
    ids.append(id)

    url = section_elem.find('a', class_='entry-title-link')['href']
    urls.append(url)
  
  return ids, works, urls

# ログ出力関数
def logging(errorLv, lambdaName, errorMsg):
  loggingDateStr=(datetime.now()).strftime('%Y/%m/%d %H:%M:%S')
  print(loggingDateStr + ' ' + lambdaName + ' [' + errorLv + '] ' + errorMsg)
  return

# index関数、存在しなければ0をreturn
def find_index(l, x):
    return l.index(x) if x in l else 0

# 以前までのMaxID、MaxWorkを取得
def get_max_data(table):
  query_data = table.get_item(
    Key = {
      'ID': SCRAPING_ID,
      'WorkTitle': WORK_TITLE
    }
  )
  max_id = query_data['Item'].get('MaxID')
  max_work = query_data['Item'].get('MaxWork')

  return max_id, max_work

#MaxDataでdynamoDBを更新
def update_max_data(table, max_id, max_work):
  if max_work:
    expression = 'set MaxWork = :w'
    value = {':w': max_work}
  else:
    expression = 'set MaxID = :i'
    value = {':i': max_id}

  table.update_item(
    Key = {
      'ID': SCRAPING_ID,
      'WorkTitle': WORK_TITLE
    },
    UpdateExpression=expression,
    ExpressionAttributeValues = value
  )
  return

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

    previous_max_id, previous_max_work = get_max_data(table) 
    
    ids,  works, urls = unique_process(soup)

    now_max_id = None if len(ids) == 0 else max(ids)
    now_max_work = None if len(works) == 0 else works[0]

    #MaxDataに違いがない場合
    if previous_max_id == now_max_id and previous_max_work == now_max_work:
        logging('success', context.function_name, 'no changes')
        return {
          'statusCode': 200,
          'body': 'not update'  
        }
    
    update_max_data(table, now_max_id, now_max_work)

    # 以前までより新しいURL
    if previous_max_id:
      new_urls = urls[:find_index(ids, previous_max_id)]
    else:
      new_urls =  urls[:find_index(works, previous_max_work)]

    new_urls.reverse()

    do_webhook(new_urls)
  
    logging('success', context.function_name, 'hooked')
    return {
      'statusCode': 200,
      'body': 'hooked'  
    }
    
  except Exception as error :
    logging('error', context.function_name, str(error))
    return {
      'statusCode': 500,
      'body': str(type(error)) + ': ' + str(error)
    }
