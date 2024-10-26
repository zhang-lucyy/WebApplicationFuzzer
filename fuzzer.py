import argparse
import mechanicalsoup

def parse_arguments():
    parser = argparse.ArgumentParser(description="Fuzzer")
    parser.add_argument("command", choices=['discover'])
    parser.add_argument("url" type=str)
    parser.add_argument("--custom-auth", type=str)
    return parser.parse_args()

def dvwa_auth(url):
    # create browser object
    browser = mechanicalsoup.StatefulBrowser()

    # Go to setup.php and reset the database
    browser.open(url + "/setup.php")
    browser.select_form('form[action="#"]')
    browser.submit_selected()
    
    # forward to login page
    browser.open(url)
    
    # Login with admin/password
    browser.select_form('form[action="login.php"]')
    browser["username"] = "admin"
    browser["password"] = "password"
    browser.submit_selected()
    
    # Set security level to Low
    browser.open(url + "/security.php")
    browser.follow_link("security.php")
    browser.select_form('form[action="security.php"]')
    browser["security"] = "low"
    browser.submit_selected()
    
    # print HTML content from home page - remove after fuzzer 0
    browser.open(url)
    print(browser.page)

def main():
    args = parse_arguments()
    
    if args.command == "discover":
        if args.custom_auth == "dvwa":
            browser = dvwa_auth(args.url)

if __name__ == "__main__":
    main()