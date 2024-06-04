import os
import requests
from datetime import datetime

# 从GitHub获取list文件
def get_lists_from_github(repo_urls):
    lists = []
    for url in repo_urls:
        response = requests.get(url)
        if response.status_code == 200:
            lists.append(response.text.split('\n'))
    return lists

# 合并多个list文件
def merge_lists(lists, custom_list=[]):
    merged_list = []
    for l in lists:
        merged_list.extend(l)
    merged_list.extend(custom_list)
    return list(set(merged_list))

# 将合并后的列表写入文件
def write_to_file(merged_list, filename):
    with open(filename, 'w') as f:
        f.write('\n'.join(merged_list))

# 主函数
def main():
    repo_urls = [
        'https://raw.githubusercontent.com/user1/repo1/main/list.txt',
        'https://raw.githubusercontent.com/user2/repo2/main/list.txt'
    ]
    custom_list = ['custom1', 'custom2']
    
    lists = get_lists_from_github(repo_urls)
    merged_list = merge_lists(lists, custom_list)
    write_to_file(merged_list, 'merged_list.txt')

if __name__ == '__main__':
    main()
