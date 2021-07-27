#!/usr/bin/env python
"""
Module to interface wodbuster webpage
"""

import sys
import os
import datetime
import time
import logging


from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By


# Create logger
logger = logging.getLogger('wodbot')


class ClassData:
    """
    Class to handle class info data
    """
    def __init__(self,
            week_day=0,
            class_type="Indra60",
            class_hour="18:10"):

        self.week_day = week_day
        self.class_type = class_type
        self.class_hour = class_hour


class UserData:
    """
    Class to handle all user data
    """
    def __init__(self, 
            web="www.test.page", 
            mail="test@mail.com",
            pssw="*****",
            class_lst=[]):

        self.web = web
        self.mail = mail
        self.pssw = pssw
        self.class_lst = class_lst


class WodBot:
    """
    Handler for wodbot
    """

    # Default delay between requests
    WEB_ACTION_WAIT = 1.0

    def __init__(self, user_data:UserData):
        # Save user data
        self.user_data = user_data
        # Create driver handler
        opts = Options()
        opts.add_argument("--headless")
        self.web_driver = Firefox(options=opts)
        logger.info("Init handler")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.web_driver:
            self.web_driver.close()

    def logging(self):
        """
        Logging into website with user datails
        """
        # Try logging into website
        logger.info("Logging into %s" % self.user_data.web)
        try:
            self.web_driver.get(self.user_data.web)
            web_element_mail = self.web_driver.find_element(By.ID, "body_body_body_body_body_IoEmail")
            web_element_pssw = self.web_driver.find_element(By.ID, "body_body_body_body_body_IoPassword")
            web_element_enter = self.web_driver.find_element(By.ID, "body_body_body_body_body_CtlEntrar")
            web_element_mail.send_keys(self.user_data.mail)
            web_element_pssw.send_keys(self.user_data.pssw)
            web_element_enter.click()
            time.sleep(self.WEB_ACTION_WAIT)
            # Browse to calendar main page
            logger.info("Go to calendar page")
            web_element_reserva = self.web_driver.find_element(By.LINK_TEXT, "Reservar clases")
            web_element_reserva.click()
            time.sleep(self.WEB_ACTION_WAIT)
        except:
            logger.error("Error on logging")
            return False
        logger.error("Logging OK")
        return True

    def findNextDay(self, next_class_date:datetime):
        """
        Search ahead in time the class specified by next_class_date
        """
        nav_tries = 0
        next_day_str = "%02d/%02d" % (next_class_date.day, next_class_date.month)
        logger.info("Next day to find: %s" % next_day_str)
        # Search next day in following 15 days
        while nav_tries < 15:
            try:
                web_element = self.web_driver.find_element(By.CSS_SELECTOR, ".mainTitle")
                if (web_element.text.find(next_day_str) != -1):
                    logger.info("Class day found")
                    return True
                else:
                    logger.debug("Date Not found, try ahead in time")
                    web_element = self.web_driver.find_element(By.CSS_SELECTOR, ".next")
                    web_element.click()
                    time.sleep(self.WEB_ACTION_WAIT)
            except:
                logger.error("Main title not found")
                return False
            nav_tries += 1
        return False

    def isCalendarActive(self):
        """
        Check if current calendar day has available classes
        """
        try:
            self.web_driver.refresh()
            web_elements = self.web_driver.find_elements(By.CSS_SELECTOR, "#calendar > div:nth-child(1) > h2:nth-child(2)")
            if len(web_elements) != 0:
                logger.debug("No class available in calendar")
            else:
                logger.debug("Class available!!")
                return True
        except:
            logger.error("Error on query")
        return False

    def getClass(self, class_data:ClassData):
        """
        Get class if matches with class_data
        """
        try:
            # Collect data from calendar
            class_index = -1
            web_elements_hora = self.web_driver.find_elements(By.CLASS_NAME, "hora")
            for element in web_elements_hora:
                if element.text.find(class_data.class_hour) != -1:
                    class_index = web_elements_hora.index(element)
            web_elements_class_type = self.web_driver.find_elements(By.CLASS_NAME, "entrenamiento")
            web_elements_get_butt = self.web_driver.find_elements(By.TAG_NAME, "button")
            # If hour found, try to get the class
            if class_index != -1:
                if (web_elements_class_type[class_index].text.find(class_data.class_type) != -1) and (web_elements_get_butt[class_index].text.find("Entrenar") != -1):
                    logger.info("Found class: %s - %s - %s" % (
                        web_elements_class_type[class_index].text,
                        web_elements_hora[class_index].text,
                        web_elements_get_butt[class_index].text,))
                    web_elements_get_butt[class_index].click()
                    time.sleep(self.WEB_ACTION_WAIT)
                    return True
                else:
                    logger.error("Error checking conditions: %s - %s - %s" % (
                        web_elements_class_type[class_index].text,
                        web_elements_hora[class_index].text,
                        web_elements_get_butt[class_index].text,))
            else:
                logger.info("Class hour not found: %s" % class_data.class_hour)
        except Exception as e:
            logger.error("Error handling webdriver")
            logger.error(e)
        return False

def getNextWeekClassDates(current_date:datetime.date):
    """
    Get a list with next week classes
    """
    logger.debug("Get next week classes")
    # Get date for next monday
    days_ahead  = 0 - current_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    class_day = current_date + datetime.timedelta(days_ahead)
    # Compute days for the entire week
    day_list = list()
    for day in range(6):
        logger.debug("Class %d: %02d/%02d" % (day, class_day.day, class_day.month))
        day_list.append(class_day)
        class_day += datetime.timedelta(1)
    return day_list


def setupLogger(logger_handler):
    """
    Setup loggers
    """
    log_filename = os.path.dirname(__file__) + "/wodbot.log"
    # Handler for error log file
    fileHandlerFormatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fileHandler = logging.FileHandler(log_filename)
    fileHandler.setFormatter(fileHandlerFormatter)
    fileHandler.setLevel(logging.DEBUG)
    # Handler for console
    consoleHandlerFormatter = logging.Formatter('%(asctime)s - %(message)s')
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(consoleHandlerFormatter)
    consoleHandler.setLevel(logging.INFO)
    # Setup logger
    logger_handler.addHandler(fileHandler)
    logger_handler.addHandler(consoleHandler)
    # Init message
    logger_handler.setLevel(logging.DEBUG)
    logger_handler.info("Init WodBot session")


def main(arguments):

    setupLogger(logger)

    # Create class list
    class_list = [
        ClassData(week_day=0, class_type="ClassName1", class_hour="18:00"),
        ClassData(week_day=1, class_type="ClassName2", class_hour="19:00"),
        ClassData(week_day=2, class_type="ClassName3", class_hour="21:00"),
        ClassData(week_day=3, class_type="ClassName4", class_hour="22:00"),
    ]

    # Generate user data
    user_account = UserData(
        web="https://testBox.wodbuster.com/user/",
        mail="test_user@test_mail.com",
        pssw="user_pssw",
        class_lst=class_list
    )

    # Get classes for next week
    class_days = getNextWeekClassDates(datetime.date.today())

    # Start process
    wodbot_handler = WodBot(user_account)
    if wodbot_handler.logging():
        if wodbot_handler.findNextDay(class_days[0]):
            # wait for available classes
            try_count = 0
            while wodbot_handler.isCalendarActive() != True:
                time.sleep(wodbot_handler.WEB_ACTION_WAIT)
                if try_count % 60 == 0:
                    logger.info("Check calendar, attemp: %d" % try_count)
                try_count += 1
            # Handle all user class days
            for class_data in user_account.class_lst:
                if wodbot_handler.findNextDay(class_days[class_data.week_day]):
                    if wodbot_handler.getClass(class_data):
                        logger.info("Get class %02d/%02d: OK" % (
                            class_days[class_data.week_day].day, 
                            class_days[class_data.week_day].month))
                        return 0
                    else:
                        logger.info("Get class %02d/%02d: ERROR" % (
                            class_days[class_data.week_day].day, 
                            class_days[class_data.week_day].month))
                        return 1
                else:
                    logger.error("Error searching for class day")
                    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
