# サイト固有のElementに対するURL, ID取得処理
def unique_process(soup):
  ids = []
  works = []
  urls = []

  a_elems = soup.find_all('a', class_='_post-list__link_18ime_25')

  for a_elem in a_elems:
    split = a_elem['href'].split('/')
    work = split[3]
    works.append(work)

    url = SCRAPING_URL + split[2] + '/' + split[3]
    urls.append(url)

  return ids, works, urls
