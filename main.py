from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time, yaml, sys
script1 = "var theForm = document.forms['QUERY'];if (!theForm) {theForm = document.QUERY;}function __doPostBack(eventTarget, eventArgument) {if (!theForm.onsubmit || (theForm.onsubmit() != false)) {theForm.__EVENTTARGET.value = eventTarget;theForm.__EVENTARGUMENT.value = eventArgument;theForm.submit();}}"

def login(driver, config):
    driver.get('https://ais.ntou.edu.tw')
    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.ID, 'M_PORTAL_LOGIN_ACNT')))
    username = driver.find_element_by_id('M_PORTAL_LOGIN_ACNT')
    username.clear()
    username.send_keys(config['account'])
    pwd = driver.find_element_by_id('M_PW')
    pwd.clear()
    pwd.send_keys(config['password'])
    driver.find_element_by_id('LGOIN_BTN').click()


def select_courses(driver, config):
    selectednum = 0
    for course in config['courses']:
        driver.get('https://ais.ntou.edu.tw/Application/TKE/TKE20/TKE2011_01.aspx')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'Div2')))
        while len(driver.find_elements_by_xpath("//div[@id='Div2']//*[contains(text(),'" + course['課號'] + "')]")) > 0:
            print(course['課號'] + ' has been added')
            selectednum += 1

        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'QUERY_COSID_BTN')))
        c = driver.find_element_by_name('Q_COSID')
        c.clear()
        c.send_keys(course['課號'])
        c.send_keys(Keys.ENTER)
        time.sleep(2)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'dv2')))
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[@id='dv2']//*[contains(text(),'查無符合資料') or contains(text(),'" + course['課號'] + "')]")))
        courselist = driver.find_elements_by_xpath("//div[@id='dv2']//tr")[1:]
        num = len(courselist)
        while num == 0:
            print('查無此課程')

        for i in range(num):
            course_text = courselist[i].text.split(' ')
            if course_text[2] == course['課號']:
                if course_text[3] == course['班別']:
                    print('[加選中]', course_text[2], course_text[3], course_text[4], course_text[6], course_text[-1])
                    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//div[@id='dv2']//a[@ml='CL_加選']")))
                    ii = courselist[i].find_element_by_css_selector('a[ml="CL_加選"]').get_attribute('href').split(':')[1]
                    driver.execute_script(script1 + ii)
                    while True:
                        try:
                            WebDriverWait(driver, 3).until(EC.alert_is_present())
                            if EC.alert_is_present():
                                courselist[i].send_keys(Keys.ENTER)
                        except:
                            pass

                    break
        else:
            return selectednum


def run(config):
    while True:
        try:
            op = webdriver.ChromeOptions()
            driver = webdriver.Chrome(chrome_options=op)
            driver.maximize_window()
            login(driver, config)
            while True:
                if select_courses(driver, config) == len(config['courses']):
                    print('all courses have been added')
                    sys.exit()
                else:
                    time.sleep(1)

        except Exception as e:
            try:
                print(e)
                driver.quit()
            finally:
                e = None
                del e

if __name__ == "__main__":
    with open('config.yaml', 'r', encoding='UTF-8') as f:
        config = yaml.load(f, Loader=(yaml.FullLoader))
    run(config)
    