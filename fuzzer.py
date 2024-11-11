import argparse
import mechanicalsoup
import urllib

def parse_arguments():
    parser = argparse.ArgumentParser(description="Fuzzer")
    parser.add_argument("command", choices=['discover'])
    parser.add_argument("url", type=str)
    parser.add_argument("--custom-auth", type=str)
    parser.add_argument("--common-words", type=argparse.FileType('r'))
    parser.add_argument("--extensions", type=argparse.FileType('r'))
    return parser.parse_args()

def dvwa_auth(url, browser):
    # Go to setup.php and reset the database
    browser.open(url + "/setup.php")
    browser.select_form('form[action="#"]')
    browser.submit_selected()
    
    # forward to login page
    browser.open(url)
    
    # Login with admin/password
    print("LOGGING INTO DVWA")
    browser.select_form('form[action="login.php"]')
    browser["username"] = "admin"
    browser["password"] = "password"
    browser.submit_selected()
    
    # Set security level to Low
    print("CHANGING SECURITY TO LOW")
    browser.open(url + "/security.php")
    browser.follow_link("security.php")
    browser.select_form('form[action="#"]')
    browser["security"] = "low"
    browser.submit_selected()
    
'''
Uses the common word list to discover potentially unlinked pages by attempting
every combination of word and extension.
'''
def guess(url, browser, args):
    browser.open(url)
    words = args.common_words.read().split("\n")
    exts = args.extensions.read().split("\n")

    # try every word / extension combo
    for word in words:
        for ext in exts:
            link = url + word + "." + ext
            page = browser.open(link)
            # link discovered
            if (page.status_code == 200):
                # add link to guessed pages set to keep track
                pages_guessed.add(link)


'''
Discovers pages on the site by finding links and visiting them.
'''
def crawl(url, browser, visited):
    # Use a queue (iterative approach) to prevent deep recursion
    to_visit = [url]
    visited.add(url)

    while to_visit:
        current_url = to_visit.pop()
        browser.open(current_url)

        for link in browser.page.select('a'):
            href = link.get("href")
            # Create absolute URL
            absolute_url = urllib.parse.urljoin(current_url, href)
            
            # Skip already visited, logout, or invalid links
            if absolute_url in visited or 'logout' in absolute_url:
                continue
            
            visited.add(absolute_url)
            to_visit.append(absolute_url)


def discover(url, browser, args):
    # correctly guessed unlinked pages
    global pages_guessed
    global visited
    pages_guessed = set()
    visited = set()

    # guess the pages if a common words list and extensions list is given
    if args.common_words and args.extensions:
        guess(url, browser, args)
        print("Pages Successfully Guessed")
        print("*" * 30)
        for link in pages_guessed:
            print(link)

    crawl(url, browser, visited)
    print("Links Discovered")
    print("*" * 30)
    for link in visited:
        print(link)
    

def main():

    args = parse_arguments()
    # create browser object
    browser = mechanicalsoup.StatefulBrowser()
    
    # login to DVWA
    if args.custom_auth == "dvwa":
        dvwa_auth(args.url, browser)
    if args.command == "discover":
        discover(args.url, browser, args)

if __name__ == "__main__":
    main()