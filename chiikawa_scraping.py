import re

# サイト固有のElementに対するURL, ID取得処理
def unique_process(soup):
  ids = []
  works = []
  urls = []

  atag_elems = soup.find_all('a', class_= 'create_time')

  for atag_elem in atag_elems:
    work = atag_elem['href']
    urls.append(work)

    id = re.findall(r'\d+', atag_elem['href'])[0]
    ids.append(id)

  return ids, works, urls
