#!/Library/Frameworks/Python.framework/Versions/3.9/bin/python3
import requests
from bs4 import BeautifulSoup
import json
import sys
import base64
import urllib.parse

def get_url(referral_page):
	response = requests.get(referral_page, headers = {'X-Requested-With': 'XMLHttpRequest', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win 64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'})
	soup = BeautifulSoup(response.text, 'html.parser')
	video_request_scripts = soup.find_all('script')
	for script in video_request_scripts:
		if str(script).find('getvidlink') > 1:
			video_script = str(script)
			break
	start = video_script.find('get(') + 5
	end = video_script.find('.then(function(response)') - 2
	vid_url = video_script[start:end]
	decoded_filename = urllib.parse.unquote(vid_url)
	trimmed_filename = decoded_filename.rsplit('&')[0].rsplit('/')[-1]
	filename = ''.join([char for char in trimmed_filename if not char.isspace()])
	page = requests.get(url + vid_url, headers = {'X-Requested-With': 'XMLHttpRequest','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}).json()
	download_url = page['cdn']+'/getvid?evid='+page['enc']
	return {'url': download_url, 'filename': filename}

def download_video(url, filename):
	r = requests.get(url, headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}, stream = True)
	with open(filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size = 1024):
			if chunk:
				f.write(chunk)
	return (filename)

def get_links(soup, desired_class):
	links = []
	i = 0
	for link in soup.find_all(class_ = desired_class):
		hit = link.find('a')
		if hit:
			links.append({'index': i, 'href': hit.get('href'), 'title': hit.get('title')})
		else:
			links.append({'index': i, 'href': link.get('href'), 'title': link.get('title')})
		i += 1
	return links

def prompt_user(dictionary):
	for option in dictionary:
		print(option['index'], '-', option['title'])

	while True:
		valid = True
		selection = []
		print('Select titles via index, separating ranges with "-" and singles with spaces.')
		user_choice = input('selection: ')
		singles = user_choice.split()
		for i in singles:
			if len(i.split('-')) == 1:
				selection.append(int(i))
			else:
				through = i.split('-')
				start = int(through[0])
				end = int(through[1])
				selection = selection + [e for e in range(start, end + 1)]

		# check that the input makes sense
		for i in selection:
			if i < len(dictionary) and i >= 0:
				continue
			else:
				print('Please enter a valid selection, or [ctrl + c] to quit.')
				valid = False

		if valid:
			break
	return selection

# get the base64 translation, strip NaN, subtract salt, chr() it.
def deobfuscate(script):
	# get the salt
	salt_split = script.split()
	alnum = []
	for string in salt_split:
		# get rid of symbols
		alnum.append(''.join([ch for ch in string if ch.isalnum()]))

	# get the one that's only numbers, it will be near the end
	for entity in alnum[::-1]:
		if entity.isnumeric():
			salt = int(entity)
			break
	try:
		print('salt:', salt)
	except Exception as e:
		print('unable to get salt:', e)
		print('abandoning attempt to download this title')
		return

	# locate the hash table
	start = script.find('[') - 1
	end = script.find(']') + 1
	table = script[start:end]
	encoded_strings = table.split(',')
	print('decrypting...')
	# base64 decode
	utf_chars = []
	for string in encoded_strings:
		base64_bytes = string.encode('ascii')
		hashed_bytes = base64.b64decode(base64_bytes)
		salted_hash = hashed_bytes.decode('ascii')
		# clean and remove salt
		clean_hash = ''.join([char for char in salted_hash if char.isnumeric()])
		if not clean_hash:
			print('could not clean hash')
			exit()
		utf_chars.append(chr(int(clean_hash) - salt))
		decrypted_content = ''.join(utf_chars)
	return BeautifulSoup(decrypted_content, 'html.parser')

if __name__ == '__main__':

	if len(sys.argv) != 2:
		print('Usage: python3', __file__, '"search query"')
		exit()

	url = 'https://www.wcostream.com'
	search = sys.argv[-1]
	post_data = {'catara': search, 'konuara':'series'}
	s = requests.Session()

	response = s.post(url + '/search', data = post_data)
	soup = BeautifulSoup(response.text, 'html.parser')

	# the class for the initial search result is 'aramadabaslik'
	links = get_links(soup, 'aramadabaslik')

	selections = prompt_user(links)
	for selection in selections:
		content_page = links[selection]['href']
		series = 'https://www.wcostream.com' + content_page
		response = s.get(series)
		soup = BeautifulSoup(response.text, 'html.parser')
		seasons = get_links(soup, 'sonra')
		downloads_index = prompt_user(seasons)
		for i in downloads_index:
			print('attempting to locate:', seasons[i]['title'])
			video_index = seasons[i]['href']
			response = s.get(video_index)
			soup = BeautifulSoup(response.text, 'html.parser')
			data = soup.find('meta', itemprop = 'embedURL')
			content = data.get('content')
			# print('content:', content)
			# get the script that loads dynamic html
			scripts = soup.find_all('script')
			scripts = [str(i) for i in scripts]
			script = max(scripts, key = len)
			# decrypt the dynamic html
			print('attempting to crack the encryption')
			html = deobfuscate(script)
			cracked = url + html.find('iframe').get('src')
			print('hidden link successfully decrypted:')
			print(cracked)
			download_data = get_url(cracked)
			print('impersonating friendly request for download link')
			filename = download_data['filename']
			download_link = download_data['url']
			print('attempting to download as', filename)
			download_video(download_link, filename)
			print('download successful!')
