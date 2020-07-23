import asyncio
import requests
from tqdm import tqdm
import csv
import numpy as np
import pandas as pd
import os


async def check_exsit(id, pid):
    df = pd.read_csv("./term.csv", delimiter='|')
    df = df.drop(['alias', 'name', 'categories', 'definition', 'source'], 1)
    r_df = df.loc[df['pid'] == pid]
    r_df = r_df.loc[df['id'] == id]
    if len(r_df.category_ids.values):
        print(f'Exsit id -> {id}')
        return r_df.category_ids.values[0]
    return None


async def tree(category):
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6",
        "Connection": "keep-alive",
        "Cookie": "JSESSIONID=168B9F4A47D7596ACFAAC82A85074AF1; zcyuid=955",
        "Host": "zcy.ckcest.cn",
        "Referer": "http://zcy.ckcest.cn/tcm/dic/sd",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.3",
        "X-Requested-With": "XMLHttpRequest"
    }
    response = requests.get(f'http://zcy.ckcest.cn/tcm/dic/treeExpand?category={category}', headers=headers)
    if response.status_code == 200:
        content = response.json()
        return [{'id': item['attr']['id'], 'name': item['data']} for item in content['results']]


async def category(name):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6",
        "Connection": "keep-alive",
        "Cookie": "JSESSIONID=CE70C134158DA4724549465B8750017E",
        "Host": "zcy.ckcest.cn",
        "Referer": "http://zcy.ckcest.cn/tcm/dic/home",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    response = requests.get(f'http://zcy.ckcest.cn/tcm/dic/NodeClass?name={name}', headers=headers)
    if response.status_code == 200:
        return response.text


async def explain(id, alias):
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,pt;q=0.6",
        "Connection": "keep-alive",
        "Cookie": "JSESSIONID=168B9F4A47D7596ACFAAC82A85074AF1; zcyuid=955",
        "Host": "zcy.ckcest.cn",
        "Referer": "http://zcy.ckcest.cn/tcm/dic/sd",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.3",
        "X-Requested-With": "XMLHttpRequest"
    }
    response = requests.get(f'http://zcy.ckcest.cn/tcm/dic/detailedInfoAjax?indexId={id}', headers=headers)
    if response.status_code == 200:
        content = response.json()
        return {
            'id': id,
            'alias': alias,
            'name': content['word']['name'],
            'category_ids': content['word']['category'],
            'categories': await category(content['word']['name']),
            'definition': content['word']['def'],
            'source': content['word']['source']
        }


async def term(id=0, name='', pid=0):
    print(f'Processing: {id} - {name} - {pid}')
    try:
        exsit_state = await check_exsit(id, pid)
        if exsit_state:
            for item in await tree(exsit_state):
                await term(item['id'], item['name'], id)
        else:
            result = await explain(id, name)

            with open('./term.csv', 'a+') as f:
                f.write(
                    f"{pid}|{result['id']}|{result['alias']}|{result['name']}|{result['category_ids']}|{result['categories']}|{result['definition']}|{result['source']}\n")

            print(
                f"{pid}|{result['id']}|{result['alias']}|{result['name']}|{result['category_ids']}|{result['categories']}|{result['definition']}|{result['source']}")

            for item in await tree(result['category_ids']):
                await term(item['id'], item['name'], id)
    except Exception as e:
        with open('./error.log', 'a+') as f:
            f.write(f"id={id} name={name} parent_id={pid}\n")
            f.write(f'{str(e)}\n\n')

        with open('./tmp.log', 'a+') as f:
            f.write(f"{id},{name},{pid}\n")


async def remove_duplicate():
    df = pd.read_csv("./term.csv", delimiter='|')
    df.sort_values("id", inplace=True)
    df.drop_duplicates(subset="id", keep=False, inplace=True)
    df.sort_values("pid", inplace=True)
    df.to_csv('./term-remove-duplicate.csv', encoding='utf-8', index=False, sep='|')
    # df.to_csv('./term-for-neo4j.csv', encoding='utf-8', index=False, quoting=1)


if __name__ == '__main__':
    if os.path.exists(f'./error.log'):
        os.remove(f'./error.log')
    if os.path.exists(f'./tmp.log'):
        os.remove(f'./tmp.log')

    # asyncio.run(remove_duplicate())

    # if not os.path.exists(f'./failed.csv'):
    #     with open('./failed.csv', 'w') as f:
    #         f.write('id,name,parent_id\n')
    # else:
    #     with open('./failed.csv') as f:
    #         for line in csv.DictReader(f, delimiter=','):
    #             asyncio.run(term(id=int(line['id']), name=line['name'], pid=int(line['parent_id'])))
    #     os.remove(f'./failed.csv')

    with open('./categories.csv') as f:
        for line in csv.DictReader(f, delimiter=','):
            if line['enable'] == '1':
                asyncio.run(term(id=int(line['id']), name=line['name']))


