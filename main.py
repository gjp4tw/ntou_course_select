import base64
import sys
import time
from typing import Tuple

import easyocr
import yaml
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

script1 = "var theForm = document.forms['QUERY'];if (!theForm) {theForm = document.QUERY;}function __doPostBack(eventTarget, eventArgument) {if (!theForm.onsubmit || (theForm.onsubmit() != false)) {theForm.__EVENTTARGET.value = eventTarget;theForm.__EVENTARGUMENT.value = eventArgument;theForm.submit();}}"


def detect_ocr(captcha_image_path: str) -> Tuple[bool, str]:
    reader = easyocr.Reader(["en"])
    result = reader.readtext("captcha.png")
    if len(result) != 1:
        return False, None

    result = result[0]

    pos, text, conf = result
    text = "".join(x for x in text if x.isalpha() or x.isnumeric())

    if len(text) != 4:
        return False, None

    return True, text


def login(driver, config):
    driver.get("https://ais.ntou.edu.tw")
    driver.refresh()
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.ID, "M_PORTAL_LOGIN_ACNT"))
    )
    username = driver.find_element(By.ID, "M_PORTAL_LOGIN_ACNT")
    username.clear()
    username.send_keys(config["account"])

    pwd = driver.find_element(By.ID, "M_PW")
    pwd.clear()
    pwd.send_keys(config["password"])

    img_base64 = driver.execute_script(
        """
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width; cnv.height = ele.height;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);    
    """,
        driver.find_element(By.ID, "PIC"),
    )
    with open("captcha.png", "wb") as image:
        image.write(base64.b64decode(img_base64))

    success, result = detect_ocr("captcha.png")

    if success:
        captcha = driver.find_element(By.ID, "M_PW2")
        captcha.send_keys(result)

    driver.find_element(By.ID, "LGOIN_BTN").click()
    driver.get("https://ais.ntou.edu.tw/title.aspx")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "USERNAME")))
    global name
    name = driver.find_element(By.ID, "USERNAME").text
    print(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        + " [訊息] 登入成功 username: "
        + name
    )


def select_courses(driver, config):
    selected = set()
    for index, course in enumerate(config["courses"]):
        if course["課號"] == "" or course["班別"] == "":
            print(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + " [錯誤] 班別或課號不可為空"
            )
            selected.add(index)
        if index in selected:
            continue
        driver.get("https://ais.ntou.edu.tw/Application/TKE/TKE20/TKE2011_01.aspx")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Div2")))
        if (
            len(
                driver.find_elements(
                    By.XPATH,
                    "//div[@id='Div2']//*[contains(text(),'" + course["課號"] + "')]",
                )
            )
            > 0
        ):
            print(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                + " [訊息] "
                + course["課號"]
                + " has been added"
            )
            selected.add(index)
            continue

        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "QUERY_COSID_BTN"))
        )
        c = driver.find_element(By.NAME, "Q_COSID")
        c.clear()
        c.send_keys(course["課號"])
        c.send_keys(Keys.ENTER)
        time.sleep(2)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "dv2")))
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@id='dv2']//*[contains(text(),'查無符合資料') or contains(text(),'"
                    + course["課號"]
                    + "')]",
                )
            )
        )
        courselist = driver.find_elements(By.XPATH, "//div[@id='dv2']//tr")[1:]
        num = len(courselist)
        if num == 0:
            print(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                + " [錯誤] "
                + "查無此課程"
            )
            selected.add(index)
            continue

        for i in range(num):
            course_text = courselist[i].text.split(" ")
            if course_text[2] == course["課號"] and course_text[3] == course["班別"]:
                print(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    + " [加選] "
                    + course_text[2]
                    + " "
                    + course_text[3]
                    + " "
                    + course_text[4]
                    + " "
                    + course_text[6]
                    + " "
                    + course_text[-1]
                )
                WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//div[@id='dv2']//a[@ml='CL_加選']")
                    )
                )
                ii = (
                    courselist[i]
                    .find_element(By.CSS_SELECTOR, 'a[ml="CL_加選"]')
                    .get_attribute("href")
                    .split(":")[1]
                )
                driver.execute_script(script1 + ii)
                while True:
                    try:
                        WebDriverWait(driver, 3).until(EC.alert_is_present())
                        if EC.alert_is_present():
                            print(
                                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                + " [錯誤] "
                                + " ".join(driver.switch_to.alert.text.split())
                            )
                            # driver.switch_to.alert.accept()
                            courselist[i].send_keys(Keys.ENTER)
                    except:
                        break
                break
    return len(selected)


def run(config):
    interval = (
        int(config["interval"])
        if (config["interval"] and int(config["interval"]) >= 300)
        else 300
    )
    T = time.time()
    while True:
        try:
            op = webdriver.ChromeOptions()
            op.add_argument("--headless")
            op.add_argument("--log-level=3")
            op.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=op)
            driver.maximize_window()
            login(driver, config)
            while True:
                if time.time() - T >= interval:
                    T = time.time()
                    print(
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        + " [訊息] 重新登入"
                    )
                    break
                if select_courses(driver, config) == len(config["courses"]):
                    print(
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        + " [訊息] all courses have been added"
                    )
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


def start():
    with open("config.yaml", "r", encoding="UTF-8") as f:
        config = yaml.load(f, Loader=(yaml.FullLoader))
    run(config)


if __name__ == "__main__":
    start()
