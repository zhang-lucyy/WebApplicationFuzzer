import argparse
import mechanicalsoup

# correctly guessed unlinked pages
global pages_guessed

# 
global visited



def parse_arguments():
    parser = argparse.ArgumentParser(description="Fuzzer")
    parser.add_argument("command", choices=['discover'])
    parser.add_argument("url", type=str)
    parser.add_argument("--custom-auth", type=str)
    parser.add_argument("--common-words", type=str)
    parser.add_argument("--extensions", type=str)
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
    if args.common_words and args.extensions:
        browser.open(url)
        words = args.common_words
        exts = args.extensions

        # try every word / extension combo
        for word in words:
            for ext in exts:
                page = browser.open(url + "/" + word + "." + ext)
                # link discovered
                if (page.status_code == 200):
                    # add link to guessed pages set to keep track
                    pages_guessed.add(url + "/" + word + "." + ext)


'''
Discovers pages on the site by finding links and visiting them.
'''
def crawl(url, browser, args):
    url = browser.absolute_url(url)
    page = browser.open(url)
    if page is not None:
        visited.add(url)

    for link in browser.links():
        href = link["href"]
        # skip links that have already been visited or the same page or logout
        if (href == "logout.php" or href in visited or href == url): continue
        crawl(href)


def discover(url):
    guess(url)
    print("Pages Guessed")
    print("*" * 15)
    for link in pages_guessed:
        print(link)

    crawl(url)
    print("Links Discovered")
    print("*" * 15)
    for link in visited:
        print(link)
    

def main():
    pages_guessed = set()
    vistited = set()

    args = parse_arguments()
    # create browser object
    browser = mechanicalsoup.StatefulBrowser()
    
    # login to DVWA
    if args.custom_auth == "dvwa":
        dvwa_auth(args.url, browser)
    if args.command == "discover":
        guess(args.url, browser, args)

if __name__ == "__main__":
    main()