# サイト固有のElementに対するURL, ID取得処理
def unique_process(soup):
  ids = []
  urls = []

  section_elems = soup.find_all('section')

  for section_elem in section_elems:
    id = section_elem['data-uuid']
    ids.append(id)

    url = section_elem.find('a', class_='entry-title-link')['href']
    urls.append(url)
  
  return ids, urls
