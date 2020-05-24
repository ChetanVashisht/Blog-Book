from selenium import webdriver
from bs4 import BeautifulSoup, Doctype
import html, time, re, requests, os, urllib, secrets
from codecs import encode, decode
import logging, argparse, subprocess, random

images = {}

def get_posts_for_year(website, year):
	url = website + "?action=getTitles&widgetId=BlogArchive1&widgetType=BlogArchive&responseType=js&path=https%3A%2F%2Fwww.ftlofaot.com%2F" + str(year)
	payload = {}
	headers = {}

	response = requests.request("GET", url, headers=headers, data = payload)
	return response.text, response.headers["content-type"]

def get_post_urls(post_js_response):
	reg = re.compile(".*('posts': \[.*?\]).*")
	c = "{" + re.search(reg, post_js_response).group(1) + "}"
	return list(map(lambda x: (x["url"]), eval(c)["posts"]))

def build_index(website):
	years = range(2009, 2021, 1)
	post_urls = []
	for year in years:
		try:
			post_js_response, content_type = get_posts_for_year(website, year)
			if (content_type == 'text/javascript; charset=UTF-8'):
				post_urls += get_post_urls(post_js_response)[::-1]
			else:
				print("No posts for published in: " + str(year))
		except Exception:
			print("Error getting posts for year: " + str(year))
			continue
	print("Index successfully built for: "+ str(len(post_urls)) + " links")
	return post_urls



def get_title(args):
	return getattr(args, "title")


def add_chapter_no(chapter, doc, body):
	hea = doc.new_tag('h1')
	hea.string = 'Chapter %d' % (chapter + 1,)
	body.append(hea)

def sleep(seconds):
	time.sleep(seconds)

def open_browser(url, driver):
	driver.get(url)

def scrape_title(driver):
	title = driver.find_element_by_css_selector(".post-title")
	return title.get_attribute("innerHTML").replace("\\n", "")

def add_chapter_title(driver, doc, body):
	ti = doc.new_tag("h1")
	ti.string = scrape_title(driver)
	body.append(ti)

def scrape_body(driver):
	content = driver.find_element_by_css_selector(".post-body")
	return BeautifulSoup(html.unescape(content.get_attribute("innerHTML")), 'html.parser')


def get_with_protocol(image_src):
	if (image_src.startswith("//")):
		return "https:" + image_src
	return image_src

def get_max_res_img_src(image_src):
	image_src = get_with_protocol(image_src)
	max_res_img_src = re.sub(r"/s\d+/", "/s10000/", image_src)
	return max_res_img_src

def get_local_image_path(image_src, images):
	return images[image_src]


def replace_element_attr(element, attr, replace_fn, *args):
	img_src = element.attrs[attr]
	max_res_img = replace_fn(element.attrs[attr], *args)
	element.attrs[attr] = max_res_img

def make_folder_if_not_present(folder):
	if not os.path.exists(folder):
		os.mkdir(folder)

def download_image(image_url, filename):
	urllib.request.urlretrieve(image_url, filename)

def get_extension(image_url):
	print(image_url)
	return re.search(r".*(\.\w+)($|\?).*", image_url).group(1)

def download_all_images_and_update_map(images, folder):
	make_folder_if_not_present(folder)
	print(images)
	for image_url in images.keys():
		filename = secrets.token_hex(16) 
		path_to_file = folder + "/" + filename + get_extension(image_url)
		download_image(image_url, path_to_file)
		images[image_url] = path_to_file

def get_image_folder_name(title):
	return "images_" + title.split(" ")[0]


def replace_absolute_image_urls(scraped, title):
	elements = scraped.find_all()
	images = {}
	for element in elements:
		attr = None
		if element.name == "img":
			attr = "src"
			replace_element_attr(element, attr, get_max_res_img_src)
			images[element.attrs[attr]] = element.attrs[attr]
		elif element.name == "a":
			attr = "href"
			replace_element_attr(element, attr, get_max_res_img_src)

	download_all_images_and_update_map(images, get_image_folder_name(title))

	for element in elements:
		attr = None
		if element.name == "img":
			attr = "src"
			replace_element_attr(element, attr, get_local_image_path, images)
			images[element.attrs[attr]] = element.attrs[attr]

	return scraped



def add_chapter_body(driver, body, title):
	scraped = scrape_body(driver)
	replaced_body = replace_absolute_image_urls(scraped, title)
	body.append(replaced_body)


def get_driver():
	return webdriver.Chrome()

def get_new_doc(args):
	doc = BeautifulSoup()
	doc.append(Doctype('html'))
	html_local = doc.new_tag('html', lang='en-US')
	doc.append(html_local)
	head = doc.new_tag('head')
	html_local.append(head)
	meta = doc.new_tag('meta', charset='utf-8')
	head.append(meta)
	title = doc.new_tag('title')
	title.string = get_title(args)
	head.append(title)
	body = doc.new_tag('body')
	html_local.append(body)
	return doc, html_local, head, body

def clean_up(driver):
	driver.close()

def store_file(filename, doc):
	with open(filename, "w") as f:
		f.write(doc.prettify())

def inputs():
	parser = argparse.ArgumentParser(description="Convert Blogs to ebooks for your kindle")
	parser.add_argument("-w", "--website", required=True, type=str, help="Url of the website you want to view. For example: http://realizingzen.blogspot.com/")
	parser.add_argument("-t", "--title", required=True, type=str, help="The title of the Book")
	parser.add_argument("-c", "--coverpage", required=False, type=str, help="Url of the coverpage. Alternatively a random one will be chosen")
	parser.add_argument("-a", "--author", required=True, type=str, help="The Author(s) of the Blog (pass authors comma separated)")
	parser.add_argument("-e", "--email", required=False, type=str, help="(Kindle) email to send the mobi")

	args = parser.parse_args()
	return args

def get_html_output_file(args):
	return get_title(args) + ".html"

def book(args):
	driver = get_driver() 
	index = build_index(getattr(args, "website"))
	title = get_title(args)
	doc, html_local, head, body = get_new_doc(args)

	for chapter, url in enumerate(index):
		try:
			print(str(chapter) + ") " + url)
			add_chapter_no(chapter, doc, body)
			sleep(1)
			open_browser(url, driver)
			add_chapter_title(driver, doc, body)
			add_chapter_body(driver, body, title)

		except Exception as e:
			logging.error('Error at %s', url, exc_info=e)


	clean_up(driver)
	htmlfile = get_html_output_file(args)
	store_file(htmlfile, doc)
	return htmlfile

def get_image_path():
	images_folder = "Wallpapers/"
	return images_folder + random.choice(os.listdir(images_folder))

def run_bash_command(bash_command):
	return subprocess.check_output(["bash", "-c", bash_command])

def get_image_output_path(image_path):
	src, ext = image_path.split(".")
	return src + "_rot." + ext

def rotate_image_if_required(image_path):
	print("Checking to rotate image: " + image_path)
	output = run_bash_command(f"identify -format '%w,%h' {image_path}")
	w, h = output.decode("utf-8").split(",")
	if w > h:
		image_output_path = get_image_output_path(image_path)
		run_bash_command(f"convert {image_path} -rotate 90 {image_output_path}")
		return image_output_path
	return image_path


def get_coverpage(args):
	if (getattr(args, "coverpage") == None):
		image_path = get_image_path()
		image_path = rotate_image_if_required(image_path)
		setattr(args, "coverpage", image_path)
	return getattr(args, "coverpage")

def get_author(args):
	return getattr(args, "author")

def compress_images(folder):
	try:
		bash_command = f"mogrify -strip -interlace Plane -gaussian-blur 0.05 -quality 85% {folder}/*"
		run_bash_command(bash_command)
	except Exception as e:
		logging.error('Error in compressing images in %s: ', folder, exc_info=e)

def generate_ebook(html_output_file, author, coverpage, title):
	mobi_output = title + ".mobi"
	image_folder = get_image_folder_name(title)
	compress_images(image_folder)
	bash_command = f"ebook-convert {html_output_file} {mobi_output} --authors {author} --publisher Anonymous --title {title} --cover '{coverpage}' --mobi-toc-at-start --toc-title 'Chapters' --language 'English-uk'"
	run_bash_command(bash_command)
	if os.path.exists(mobi_output):
		return mobi_output
	return None

def get_email(args):
	return getattr(args, "email")

def send_email_to(email, attachment):
	bash_command = f"node emailing/emailer.js -t {email} -a {attachment} -s 'Blog<->Book for Kindle' --html '<s>PFA: Blog -> Book</s>'"
	print(bash_command)
	run_bash_command(bash_command)

def email_book(book_path, args):
	email = get_email(args)
	if email != None and book_path != None:
		send_email_to(email, book_path)


if __name__ == '__main__':
	args = inputs()
	print(args)
	title = get_title(args)
	html_output_file = book(args)
	author = get_author(args)
	coverpage = get_coverpage(args)
	mobi = generate_ebook(html_output_file, author, coverpage, title)
	email_book(mobi, args)

