#!/usr/bin/env python3
from operator import truediv
from pickle import TRUE
from jinja2 import Undefined
import requests
from bs4 import BeautifulSoup
import json
import sys
import time
import base64
import urllib.parse
import re
import os


def check_special(videos, video_index):
    if(re.search("[S|s]pecial", videos[video_index]["title"])):
        return " special"
    else:
        return ""


def check_ova(videos, video_index):
    if(re.search("ova", videos[video_index]["title"].lower())):
        return " OVA"
    else:
        return ""


def confirm_name(original_filename, filename, skip):
    while True:
        print()
        print("Original name: ")
        print(original_filename)
        if not skip:
            print(
                "Is the following filename correct(REMEMBER FILETYPE EXTENSION)?[y/N]")
            print(filename)
            if input().lower() == "y":
                return filename
            else:
                print("Enter new name")
                filename = input()
        else:
            skip = False
            print("Enter new name")
            filename = input()


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def prompt_modifier(message, modifier, current_selection):
    if modifier == Undefined:
        print("Specials/ova's can have weird naming. Use reference thetvdb.com for finding out the number of the first special episode (should be in season 0)")
        print("Find out what this first special should be numbered and the rest will hopefully be figured out")
        print(message)
        while True:
            response = input().lower()
            try:
                return response - current_selection
            except:
                print("Input must be a number, try again:")


def add_structure(videos, show_name, selections, full_auto, manual_speicals):
    # print("asdadasd")
    # print(selections)
    # print(videos)
    modifier = Undefined
    create_dir(show_name)
    for video_index in selections:
        video_numbers = re.findall("(?<= )\d+", videos[video_index]["title"])
        # print("Video title: ", videos[video_index]["title"])
        # print("Video numbers: ", video_numbers)
        if(len(video_numbers) == 1):
            video_numbers.append(video_numbers[0])
            video_numbers[0] = 1
        if(len(video_numbers) > 2 or len(video_numbers) < 1):
            if(len(video_numbers) < 1):
                video_numbers.append("0")
            print("Could not find episode nrs, enter a file name manually:")
            filename = confirm_name(videos[video_index]['filename'],
                                    videos[video_index]['filename'], TRUE)
        else:
            if check_special(videos, video_index) or check_ova(videos, video_index):
                modifier = prompt_modifier(
                    "This is mostly guesswork, so it might not be(probably isn't) correct", modifier, video_index)
                video_numbers[0] = 0
                special_number = video_index + modifier
                filename = show_name + " S" + str(video_numbers[0]) + "E" + \
                    str(special_number) + check_ova(videos, video_index) + check_special(videos, video_index) + "." + \
                    videos[video_index]["filetype"]
                if manual_special:
                    confirm_name(videos[video_index]
                                 ['filename'], filename, False)
                else:
                    print(
                        "It is HIGHLY suggested to at least doublecheck a correct name for specials/ovas, are you sure you don't want to doublecheck?[y/N]")
                    if input().lower == "y":
                        confirm_name(videos[video_index]
                                     ['filename'], filename, False)
            else:
                filename = show_name + " S" + str(video_numbers[0]) + "E" + \
                    str(video_numbers[1]) + check_ova(videos, video_index) + check_special(videos, video_index) + "." + \
                    videos[video_index]["filetype"]
            if not full_auto:
                filename = confirm_name(
                    videos[video_index]['filename'], filename, False)

        dir = show_name + "/" + str(video_numbers[0]) + "/"
        create_dir(dir)
        print("Moving \"" + videos[video_index]
              ['filename'] + "\" to \"" + dir + filename)
        os.rename(videos[video_index]['filename'], dir + filename)


def get_url(session, referral_page):
    global rate
    print('Accessing the decrypted link.')
    while True:
        try:
            print('waiting for', rate, 'seconds.')
            time.sleep(rate)
            response = session.get(referral_page, headers={
                'X-Requested-With': 'XMLHttpRequest', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win 64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(e)
            print('limiting request rates by +60s.')
            rate += 60
            continue
        break

    video_request_scripts = soup.find_all('script')
    for script in video_request_scripts:
        if str(script).find('getvidlink') > 1:
            video_script = str(script)
            break
    start = video_script.find('get(') + 5
    end = video_script.find('.then(function(response)') - 2
    vid_url = video_script[start: end]
    decoded_filename = urllib.parse.unquote(vid_url)
    trimmed_filename = decoded_filename.rsplit('&')[0].rsplit('/')[-1]
    filename = ''.join(
        [char for char in trimmed_filename if not char.isspace()])
    print('Requesting the download link.')
    while True:
        print('waiting for', rate, 'seconds.')
        time.sleep(rate)
        try:
            page = session.get(url + vid_url, headers={'X-Requested-With': 'XMLHttpRequest',
                                                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}).json()
            download_url = page['cdn']+'/getvid?evid='+page['enc']
            alt_url = page['server']+'/getvid?evid='+page['enc']
        except Exception as e:
            print(e)
            print('limiting request rates by +60s.')
            rate += 60
            continue
        break

    if filename and download_url:
        return {'url': download_url, 'filename': filename, 'alt_url': alt_url}
    else:
        raise Exception('Either download_url or filename are blank.')


def download_video(session, url, alt_url, filename):
    global rate
    print('waiting for', rate, 'seconds.')
    time.sleep(rate)
    try:
        r = session.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}, stream=True)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return (filename)
    except:
        r = session.get(alt_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'}, stream=True)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return (filename)


def get_links(soup, desired_class):
    links = []
    i = 0
    for link in soup.find_all(class_=desired_class)[::-1]:
        hit = link.find('a')
        if hit:
            links.append({'index': i, 'href': hit.get('href'),
                         'title': hit.get('title').lstrip('Watch')})
        else:
            links.append({'index': i, 'href': link.get('href'),
                         'title': link.get('title').lstrip('Watch')})
        i += 1
    return links


def prompt_user(dictionary):
    for option in dictionary:
        print(option['index'], '-', option['title'])

    while True:
        valid = True
        selection = []
        print(
            'Select titles via index, separating ranges with "-" and singles with spaces.')
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
    # print(salt_split)
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
        return e

    # locate the hash table
    start = script.find('[') - 1
    end = script.find(']') + 1
    table = script[start:end]
    encoded_strings = table.split(',')
    print('decrypting...')
    # base64 decode
    utf_chars = []
    for string in encoded_strings:
        # print('string:', string)
        base64_bytes = string.encode('ascii')
        hashed_bytes = base64.b64decode(base64_bytes)
        salted_hash = hashed_bytes.decode('ascii')
        # clean and remove salt
        clean_hash = ''.join(
            [char for char in salted_hash if char.isnumeric()])
        try:
            clean_hash
        except Exception as e:
            return e
        utf_chars.append(chr(int(clean_hash) - salt))
        decrypted_content = ''.join(utf_chars)
        # print(decrypted_content)
    return BeautifulSoup(decrypted_content, 'html.parser')


if __name__ == '__main__':
    autorename_on = False
    full_auto = False
    for_plex = False
    manual_special = True
    if len(sys.argv) != 2:
        print('Usage: python3', __file__, '"search query"')
        exit()

    global rate
    rate = 0
    url = 'https://www.wcostream.com'
    search = sys.argv[-1]
    post_data = {'catara': search, 'konuara': 'series'}

    s = requests.Session()

    response = s.post(url + '/search', data=post_data)
    soup = BeautifulSoup(response.text, 'html.parser')

    # the class for the initial search result is 'aramadabaslik'
    links = get_links(soup, 'aramadabaslik')
    if len(links) == 0:
        print('No results.')
        exit()

    selections = prompt_user(links)
    for selection in selections:
        content_page = links[selection]['href']
        series = 'https://www.wcostream.com' + content_page

        while True:
            print('waiting for', rate, 'seconds.')
            time.sleep(rate)
            try:
                response = s.get(series)
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                print(e)
                print('limiting request rates by +60s')
                rate += 60
                continue
            break

        seasons = get_links(soup, 'sonra')
        downloads_index = prompt_user(seasons)
        print(
            "Do you want to autorename the videos?(You will be able to get prompted with every name)[y/N]")
        if(input().lower() == "y"):
            autorename_on = True
            print("Do you want it organised for plex?[y/N]")
            print(
                "Plex handles specials and ova's badly, so if you are not using it with plex, respond with n")
            if(input().lower() == "y"):
                for_plex = True
            print(
                "Do you want to confirm every name manually?(to do only specials answer no here)[Y/n]")
            if(for_plex):
                print("HIGHLY recommended you confirm at least all OVAs/Specials manully since figuring out the right name for specials/OVAs for plex is inaccurate")
            if input().lower() == "n":
                print("Do you want to confirm just the specials/OVAs?[Y/n]")
                if input().lower() == "n":
                    manual_special = False
                print(
                    "You understand that full-auto/semi-auto renaming might name a file wrong and that there is no undo?[\"yes\"/\"No\"]")
                while True:
                    answer = input().lower()
                    if answer == "yes":
                        full_auto = True
                        break
                    elif answer == "no":
                        break
                    else:
                        print("Either \"yes\" or \"no\" has to be typed out")

        for i in downloads_index:
            print('attempting to locate:', seasons[i]['title'])
            video_index = seasons[i]['href']

            while True:
                print('waiting for', rate, 'seconds.')
                time.sleep(rate)
                try:
                    response = s.get(video_index)
                    soup = BeautifulSoup(response.text, 'html.parser')
                except Exception as e:
                    print(e)
                    print('limiting request rates by +60s')
                    rate += 60
                    continue
                break

            # get the script that loads the dynamic html
            print('Attempting to locate the encrypted content.')
            try:
                scripts = soup.find_all('script')
                scripts = [str(i) for i in scripts]
                script = max(scripts, key=len)
                script
            except Exception as e:
                print(e)
                print('unable to find the encrypted content, skipping.')
                continue

            # decrypt the dynamic html
            print('attempting to crack the encryption.')
            try:
                html = deobfuscate(script)
                cracked = url + html.find('iframe').get('src')
                cracked
            except Exception as e:
                print(e)
                print('Unable to decrypt request link, skipping.')
                continue

            # request the actual video link
            try:
                download_data = get_url(s, cracked)
                # filename = download_data['filename']
                filename = ''.join([
                    x for x in download_data['filename'] if x.isalnum()
                    or x == '.'
                ])
                temp = filename.split('.')
                seasons[i]['filetype'] = temp[len(temp) - 1]
                download_link = download_data['url']
                alt_url = download_data['alt_url']
            except Exception as e:
                print(e)
                print('skipping.')
                continue

            print('attempting to download video.')
            try:
                seasons[i]['filename'] = download_video(
                    s, download_link, alt_url, filename)
            except Exception as e:
                print(e)
                print('skipping.')
                continue
            print('Successfully downloaded:', filename)
            print()
    if(autorename_on):
        add_structure(seasons, search, downloads_index,
                      full_auto, manual_special)
    exit()
