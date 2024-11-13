import argparse
import mechanicalsoup
import urllib.parse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Fuzzer')
    parser.add_argument('command', choices=['discover'])
    parser.add_argument('url', type=str)
    parser.add_argument('--custom-auth', type=str)
    parser.add_argument('--common-words', type=argparse.FileType('r'))
    parser.add_argument('--extensions', type=argparse.FileType('r'))
    return parser.parse_args()

def dvwa_auth(url, browser):
    # Go to setup.php and reset the database
    browser.open(url + '/setup.php')
    browser.select_form('form[action="#"]')
    browser.submit_selected()
    
    # forward to login page
    browser.open(url)
    
    # Login with admin/password
    print('LOGGING INTO DVWA')
    browser.select_form('form[action="login.php"]')
    browser['username'] = 'admin'
    browser['password'] = 'password'
    browser.submit_selected()
    
    # Set security level to Low
    print('CHANGING SECURITY TO LOW')
    browser.open(url + '/security.php')
    browser.follow_link('security.php')
    browser.select_form('form[action="#"]')
    browser['security'] = 'low'
    browser.submit_selected()
    
'''
Uses the common word list to discover potentially unlinked pages by attempting
every combination of word and extension.
'''
def guess(url, browser, args):
    browser.open(url)
    words = args.common_words.read().split('\n')
    exts = args.extensions.read().split('\n')

    # try every word / extension combo
    for word in words:
        for ext in exts:
            link = url + word + '.' + ext
            page = browser.open(link)
            # link discovered
            if (page.status_code == 200):
                # add link to guessed pages set to keep track
                pages_guessed.add(link)

'''
Discovers pages on the site by finding links and visiting them.
'''
def crawl(url, base_url, browser, visited):
    if url in visited or 'logout' in url.lower():
        return
        
    # Try to open the page
    browser.open(url)
    
    # Process each link on the page
    for link in browser.page.select('a'):
        href = link.get('href')
        # make sure link does not go off site and skip logout link
        if (urllib.parse.urlparse(href).scheme != 'http' and urllib.parse.urlparse(href).scheme != 'https' and 'logout' not in href.lower()):
            current_link = base_url + href
            # add link if not already visited
            if (current_link not in visited):
                page = browser.open(current_link)
                if (page.status_code == 200):
                    visited.add(current_link)
                    crawl(current_link, base_url, browser, visited)
            

def discover(url, browser, args):
    # correctly guessed unlinked pages
    global pages_guessed
    pages_guessed = set()

    # links crawled
    global visited
    visited = set()

    # original site link
    global base_url
    base_url = url

    # guess the pages if a common words list and extensions list is given
    if args.common_words and args.extensions:
        guess(url, browser, args)
        print('Pages Successfully Guessed')
        print('*' * 40)
        for link in pages_guessed:
            print(link)

    # link crawling
    crawl(url, base_url, browser, visited)
    print('Links Discovered')
    print('*' * 40)
    for link in visited:
        print(link)
    

def main():
    args = parse_arguments()

    # create browser object
    browser = mechanicalsoup.StatefulBrowser()
    
    # login to DVWA
    if args.custom_auth == 'dvwa':
        dvwa_auth(args.url, browser)
    if args.command == 'discover':
        discover(args.url, browser, args)

if __name__ == '__main__':
    main()