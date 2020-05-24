from selenium import webdriver
import html, time
from bs4 import BeautifulSoup, Doctype



driver = webdriver.Chrome()
driver.get("https://camunda.com/best-practices/estimating-effort/")

doc = BeautifulSoup()
doc.append(Doctype('html'))
html_local = doc.new_tag('html', lang='en-US')
doc.append(html_local)
head = doc.new_tag('head')
html_local.append(head)
meta = doc.new_tag('meta', charset='utf-8')
head.append(meta)
title = doc.new_tag('title')
title.string = 'Camunda Book'
head.append(title)
body = doc.new_tag('body')
html_local.append(body)



try:
	time.sleep(1)
	title = driver.find_element_by_class_name("page-title")
	ti = doc.new_tag("h1")
	ti.string = title.get_attribute("innerHTML")
	body.append(ti)

	content = driver.find_element_by_class_name("content-text")
	b = BeautifulSoup(html.unescape(content.get_attribute("innerHTML")), 'html.parser')
	body.append(b)

	with open("/Users/thechetan/Desktop/out.html", "w") as f:
		f.write(doc.prettify())

finally:
	driver.close()