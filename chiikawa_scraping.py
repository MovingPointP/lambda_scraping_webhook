import re

# サイト固有のElementに対するURL, ID取得処理
def unique_process(soup):
  ids = []
  works = []
  urls = []

  a_elems = soup.find_all('a', class_= 'create_time')

  for a_elem in a_elems:
    url = a_elem['href'].replace('twitter.com', 'fxtwitter.com').replace('x.com', 'fixupx.com')
    urls.append(url)

    id = re.findall(r'\d+', a_elem['href'])[0]
    ids.append(id)

  return ids, works, urls
