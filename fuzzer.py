import argparse
import mechanicalsoup
from urllib.parse import parse_qs, urljoin, urlparse

'''
Declares the parameters for the Web Application Fuzzer.
'''
def parse_arguments():
    parser = argparse.ArgumentParser(description='Fuzzer')
    parser.add_argument('command', choices=['discover', 'test'])
    parser.add_argument('url', type=str)
    parser.add_argument('--custom-auth', type=str)
    parser.add_argument('--common-words', type=argparse.FileType('r'), required=True)
    parser.add_argument('--extensions', type=argparse.FileType('r'))
    parser.add_argument('--vectors', type=argparse.FileType('r'), required=True)
    parser.add_argument('--sanitized_chars', type=argparse.FileType('r'))
    parser.add_argument('--sensitive', type=argparse.FileType('r'), required=True)
    parser.add_argument('--slow', type=int, default=500)
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
every combination of word and extension. Part of Fuzzer Discover.
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
Part of Fuzzer Discover.
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
Part of Fuzzer Discover.
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
                    type = input.get('type')
                    dict = {
                        'title': page_title,
                        'name': name,
                        'value': value,
                        'type': type,
                        'url': link
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

    print('----------DISCOVER----------')
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

'''
Given the status code of a request, it translates the code to be human readable.
'''
def get_status_code(code):
    if code == 200:
        return 'Success (OK)'
    elif code == 301:
        return 'Moved Permanently'
    elif code == 302:
        return 'Found (Redirect)'
    elif code == 303:
        return 'See Other (Redirect)'
    elif code == 400:
        return 'Bad Request'
    elif code == 401:
        return 'Unauthorized'
    elif code == 403:
        return 'Forbidden'
    elif code == 404:
        return 'Not Found'
    elif code >= 500 and code <= 599:
        return 'Server Error'
    else:
        return 'Unknown'
    
'''
Testing with a list of fuzz vectors to determine if there are any errors in the outcome
which includes lack of sanitization, sensitive data leaks, delayed responses, or http response codes.
'''
def test(args, browser):
    print('----------TESTING----------')
    print('May take a bit if lots of inputs to test...hang in there...')
    vectors = args.vectors.read().split('\n')

    # if a sanitized file is provided
    if args.sanitized_chars:
        sanitized = args.sanitized_chars.read().split('\n')
    else:
        sanitized = ['<', '>'] # default

    sensitive = args.sensitive.read().split('\n')

    slow = args.slow

    # num of unsanitizied inputs
    unsanitized = set()
    # num of possible senesitve data leakages
    sensitive_leak = set()
    # num of possible dos vulnerabilities
    delayed = set()
    # num of http/response code errors
    http_errors = set()
    # ensures that if an input is already declared unsanitized, it won't test again 
    tested = set()
    # ensures that no duplicate links are tested
    processed = set()

    form_inputs = form_parameters(browser)

    # iterates over form inputs
    for page_inputs in form_inputs:
        for input in page_inputs:   # iterate over all the dicts of inputs
            name = input['name']
            url = input['url']

            if (input['type'] == 'file'):
                continue
            else:
                for vector in vectors:
                    browser.open(url)
                    browser.select_form('form')
                    browser[name] = vector
                    page = browser.submit_selected()

                    # check for delayed responses
                    if page.elapsed.total_seconds() * 1000 > float(slow) and url not in processed:
                        delayed.add((url, str(page.elapsed.total_seconds())))
                        processed.add(url)

                    # check for http errors
                    if page.status_code != 200:
                        http_errors.add((url, str(page.status_code), get_status_code(page.status_code)))

                    # check for sensitive data
                    for data in sensitive:
                        if data in page.text:
                            sensitive_leak.add((url, data))

                    # check for sanitization
                    for char in sanitized:
                        if char in page.text and name not in tested:
                            unsanitized.add((url, name))
                            tested.add(name)

    # checking for pages that don't have any inputs
    for link in visited:
        for vector in vectors:
            if '?' in link:  # inputs that are discoverable via url parsing
                base_url, query = link.split('?', 1)
                param, value = query.split('=', 1)
                link = base_url + '?' + param + '=' + vector

            page = browser.open(link)

            if page is not None:
                # check for delayed responses
                if page.elapsed.total_seconds() * 1000 > float(slow) and link not in processed:
                    delayed.add((link, str(page.elapsed.total_seconds())))
                    processed.add(link)

                # check for http errors
                if page.status_code != 200:
                    http_errors.add((link, str(page.status_code), get_status_code(page.status_code)))

                # check for sensitive data
                for data in sensitive:
                    if data in page.text:
                        sensitive_leak.add((link, data))

                # check for sanitization
                if '?' in link:
                    for char in sanitized:
                        if char in page.text and param not in tested:
                            unsanitized.add((link, param))
                            tested.add(param)
    
    print('Lacks Sanitization:')
    print('*' * 40)
    if (len(unsanitized) == 0):
        print('None')
    else:
        for tuple in unsanitized:
            print('Page: ' + tuple[0] + ' - Input: ' + tuple[1])
        print('Total: ' + str(len(unsanitized)))

    print('Sensitive Data Leaks:')
    print('*' * 40)
    if (len(sensitive_leak) == 0):
        print('None')
    else:
        for tuple in sensitive_leak:
            print('Page: ' + tuple[0] + ' leaks sensitive data of ' + tuple[1])
        print('Total: ' + str(len(sensitive_leak)))

    print('Delayed Responses:')
    print('*' * 40)
    if (len(delayed) == 0):
        print('None')
    else:
        for tuple in delayed:
            print('Page: ' + tuple[0] + ' takes ' + tuple[1] + ' secs to load')
        print('Total: ' + str(len(delayed)))

    print('HTTP Response Codes:')
    print('*' * 40)
    if (len(http_errors) == 0):
            print('None')
    else:
        for tuple in http_errors:
            print(tuple[1] + ' => ' + tuple[2] + ' for ' + tuple[0])
        print('Total: ' + str(len(http_errors)))

def main():
    args = parse_arguments()

    # create browser object
    browser = mechanicalsoup.StatefulBrowser()
    
    # login to DVWA
    if args.custom_auth == 'dvwa':
        dvwa_auth(args.url, browser)
    if args.command == 'discover':
        discover(args.url, browser, args)
    if args.command == 'test':
        discover(args.url, browser, args)
        test(args, browser)

if __name__ == '__main__':
    main()