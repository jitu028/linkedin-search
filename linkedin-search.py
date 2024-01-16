from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import parameters, csv, os.path, time

# Add a function to initialize the driver for the selected browser
def get_driver(browser_name):
    if browser_name.lower() == 'chrome':
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    elif browser_name.lower() == 'firefox':
        return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    elif browser_name.lower() == 'edge':
        return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
    # For Safari, Service is not required
    elif browser_name.lower() == 'safari':
        return webdriver.Safari()
    else:
        raise ValueError(f"Browser '{browser_name}' is not supported.")


# Functions
def search_and_send_request(keywords, till_page, writer, ignore_list=[]):
    for page in range(1, till_page + 1):
        print('\nINFO: Checking on page %s' % page)
        query_url = 'https://www.linkedin.com/search/results/people/?keywords=' + keywords + '&origin=GLOBAL_SEARCH_HEADER&page=' + str(page)
        driver.get(query_url)
        time.sleep(5)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'reusable-search__result-container')))
        html = driver.find_element(By.TAG_NAME, 'html')
        html.send_keys(Keys.END)
        time.sleep(5)
        linkedin_urls = driver.find_elements(By.CLASS_NAME, 'reusable-search__result-container')
        print('INFO: %s connections found on page %s' % (len(linkedin_urls), page))
        for index, result in enumerate(linkedin_urls, start=1):
            text = result.text.split('\n')[0]
            if text in ignore_list or text.strip() in ignore_list:
                print("%s ) IGNORED: %s" % (index, text))
                continue
            connection_action = result.find_elements(By.CLASS_NAME, 'artdeco-button__text')
            if connection_action:
                connection = connection_action[0]
            else:
                print("%s ) CANT: %s" % (index, text))
                continue
            if connection.text == 'Connect':
                try:
                    coordinates = connection.location_once_scrolled_into_view  # returns dict of X, Y coordinates
                    driver.execute_script("window.scrollTo(%s, %s);" % (coordinates['x'], coordinates['y']))
                    time.sleep(5)
                    connection.click()
                    time.sleep(5)
                    if driver.find_elements(By.CLASS_NAME, 'artdeco-button--primary')[0].is_enabled():
                        driver.find_elements(By.CLASS_NAME, 'artdeco-button--primary')[0].click()
                        writer.writerow([text])
                        print("%s ) SENT: %s" % (index, text))
                    else:
                        driver.find_elements(By.CLASS_NAME, 'artdeco-modal__dismiss')[0].click()
                        print("%s ) CANT: %s" % (index, text))
                except Exception as e:
                    print('%s ) ERROR: %s' % (index, text))
                time.sleep(5)
            elif connection.text == 'Pending':
                print("%s ) PENDING: %s" % (index, text))
            else:
                if text:
                    print("%s ) CANT: %s" % (index, text))
                else:
                    print("%s ) ERROR: You might have reached limit" % (index))

driver = None
try:
    # Login
    # Select browser
    browser_name = parameters.browser_name  # Add browser_name in your parameters file
    driver = get_driver(browser_name)
    driver.get('https://www.linkedin.com/login')
    driver.find_element('id', 'username').send_keys(parameters.linkedin_username)
    driver.find_element('id', 'password').send_keys(parameters.linkedin_password)
    driver.find_element('xpath', '//*[@type="submit"]').click()
    time.sleep(10)
    # CSV file loging
    file_name = parameters.file_name
    file_exists = os.path.isfile(file_name)
    writer = csv.writer(open(file_name, 'a'))
    if not file_exists: writer.writerow(['Connection Summary'])
    ignore_list = parameters.ignore_list
    if ignore_list:
        ignore_list = [i.strip() for i in ignore_list.split(',') if i]
    else:
        ignore_list = []
    # Search
    search_and_send_request(keywords=parameters.keywords, till_page=parameters.till_page, writer=writer,
                            ignore_list=ignore_list)
except KeyboardInterrupt:
    print("\n\nINFO: User Canceled\n")
except Exception as e:
    print('ERROR: Unable to run, error - %s' % (e))
finally:
    # Close browser
    if driver is not None:
        driver.quit()

