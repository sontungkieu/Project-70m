from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import csv

def travel_distance(origin, destination, filename):
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    
    driver.get("https://www.google.com/maps/dir/")
    time.sleep(2)
    
    input_element = driver.find_elements(By.CLASS_NAME, "tactile-searchbox-input")
   
    input_element[0].send_keys(origin)
    input_element[1].send_keys(destination + Keys.ENTER)
    
    time.sleep(3)
    
    try:
        distance_element = driver.find_element(By.XPATH,"//div[contains(@class, 'ivN21e tUEI8e fontBodyMedium')]" )  # Adjust if needed
        distance_text = distance_element.text
    except:
        distance_text = "Not Found"
    driver.quit()
    
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([origin, destination, distance_text])


    
    
