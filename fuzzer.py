import argparse
import mechanicalsoup
from urllib.parse import urljoin, urlparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Fuzzer')
    parser.add_argument('command', choices=['discover'])
    parser.add_argument('url', type=str)
    parser.add_argument('--custom-auth', type=str)
    parser.add_argument('--common-words', type=argparse.FileType('r'), required=True)
    parser.add_argument('--extensions', type=argparse.FileType('r'))
    return parser.parse_args()

'''
Logs into DVWA.
'''
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
    # correctly guessed unlinked pages
    global pages_guessed 
    pages_guessed = set()

    browser.open(url)
    # read the word and extensions files
    words = args.common_words.read().split('\n')

    # default to php and empty string if extensions file is not specified
    if args.extensions:
        exts = args.extensions.read().split('\n')
    else:
        exts = ['.php', ''] # default

    # try every word / extension combo
    for word in words:
        for ext in exts:
            link = url + word + ext
            page = browser.open(link)
            # link discovered
            if (page.status_code == 200):
                # add link to guessed pages set to keep track
                pages_guessed.add(link)

'''
Discovers pages on the site by finding links and visiting them.
'''
def crawl(url, base_url, browser, visited):
    try:
        page = browser.open(url)

        if page.status_code == 200 and browser.page:
            # Process each link on the page
            for link in browser.page.select('a'):
                href = link.get('href')
                
                # make sure link does not go off site and skip logout link
                if href and (urlparse(href).scheme not in ('http', 'https') and 'logout' not in href.lower()):
                    current_link = urljoin(base_url, href)
                    # add link if not already visited
                    if (current_link not in visited):
                        page = browser.open(current_link)
                        if (page.status_code == 200):
                            visited.add(current_link)
                            crawl(current_link, base_url, browser, visited)
    except:
        return


'''
Attempts to discover every possible input fields to forms for each page.
'''
def form_parameters(browser):
    # form inputs for ALL links
    form_inputs = []

    for link in visited:
        browser.open(link)
        if browser.page is not None:
            page_title = browser.page.find('title')
            inputs = browser.page.find_all(['input', 'textarea'])

            # list of all inputs for ONE page specifically
            input_list = []
            for input in inputs:
                # gets ALL input fields to a form, skipping buttons/submits
                if (input.get('type') not in ['button', 'submit']):
                    name = input.get('name')
                    value = input.get('value')
                    dict = {
                        'title': page_title,
                        'name': name,
                        'value': value,
                    }
                    input_list.append(dict)
            if (len(input_list) > 0):
                form_inputs.append(input_list)
    
    return form_inputs
            
'''
Discovers as many potential inputs to the system as possible including page 
discovery and input discovery.
'''
def discover(url, browser, args):
    # links crawled
    global visited
    visited = set()

    # original site link
    global base_url
    base_url = url

    # page discovery
    guess(url, browser, args)
    print('Pages Successfully Guessed:')
    print('*' * 40)
    for link in pages_guessed:
        print(link)

    # link crawling from initial url
    crawl(url, base_url, browser, visited)

    # link crawling from pages guessed
    for page in pages_guessed:
        if page not in visited:
            visited.add(page)
            crawl(page, base_url, browser, visited)

    # print all crawled links
    print('Links Discovered:')
    print('*' * 40)
    for link in visited:
        print(link)

    # input discovery
    # parse URLs
    print('Parsed URLs:')
    print('*' * 40)
    for link in visited:
        if ('?' in link):
            parse = link.split('?')
            print(parse)
        else:
            print([link])
    print('*' * 40)

    # form inputs
    form_params = form_parameters(browser)
    for param in form_params:
        title = (param[0]['title']).string
        print('Page: ' + str(title))
        print('*' * 40)
        print('Form Inputs:')
        print('************')
        print("{:<30}{:^10}".format('Name:', 'Value:'))
        for dict in param:
            name = str(dict['name'])
            value = str(dict['value'])
            print("{:<30}{:^10}".format(name, value))
        print('*' * 40)

    # Cookies
    print('Cookies:')
    print('*' * 40)
    cookies = browser.get_cookiejar()
    for cookie in cookies:
        print(cookie)
    print('*' * 40)

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