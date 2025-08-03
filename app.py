from flask import Flask, jsonify, request, send_file, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import subprocess
import os
import time
import logging
import base64
import random
import uuid
import traceback
from dotenv import load_dotenv
import re
from io import BytesIO


load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

API_KEYS = [
    "sman-apiA1B2C3D4E5",
    "sman-apiF6G7H8I9J0",
    "sman-apiK1L2M3N4O5",
    "sman-apiP6Q7R8S9T0",
    "sman-apiU1V2W3X4Y5",
    "sman-apiZ6A7B8C9D0",
    "sman-apiE1F2G3H4I5",
    "sman-apiJ6K7L8M9N0",
    "sman-apiO1P2Q3R4S5",
    "sman-apiT6U7V8W9X0"
]

#=====BAD PROMPTS=======#
bad_words = [
    # 🔞 SEXUAL / EXPLICIT
    "sex", "porn", "porno", "pornography", "nude", "nudity", "boobs", "tits", "breasts",
    "vagina", "pussy", "dick", "cock", "penis", "cum", "clit", "orgasm", "blowjob",
    "handjob", "masturbate", "masturbation", "anal", "anus", "butthole", "suck",
    "slut", "whore", "hoe", "bitch", "milf", "hentai", "bdsm", "xxx", "deepthroat",
    "fingering", "fuck", "fucked", "fucker", "fucking", "lick", "licking", "horny",
    "erotic", "rape", "rapist", "incest", "molest", "molester", "ejaculate", "ejaculation",

    # 💀 VIOLENT / HARMFUL
    "kill", "murder", "assassinate", "slaughter", "stab", "shoot", "gun", "bomb",
    "explosive", "terror", "terrorist", "suicide", "hang", "cut", "slice",
    "harm", "abuse", "torture", "die", "dead", "corpse", "blood", "explode", "burn",
    "lynch", "strangle", "suffocate", "decapitate", "execute", "sacrifice", "fight",
    "fighting", "behead", "violence", "poison", "selfharm", "overdose", "slit",
    "kidnap", "hostage", "bludgeon", "chainsaw", "genocide", "killself",

    # 🧠 MENTAL HEALTH / SELF-HARM
    "depress", "depressed", "depression", "anxiety", "panic", "kill myself",
    "want to die", "suicidal", "selfharm", "cutting", "hurt myself", "overdose",
    "hate myself", "i'm worthless", "i want to disappear", "burn myself",
    "jump off", "kill me", "i'm done", "slit wrists", "end my life",

    # 🧑‍⚖️ CRIME / ILLEGAL
    "steal", "thief", "rob", "robbery", "scam", "fraud", "cheat", "piracy", "pirate",
    "forgery", "fake id", "counterfeit", "hack", "hacker", "phishing", "blackmail",
    "drug", "cocaine", "meth", "weed", "heroin", "marijuana", "smuggle", "bribe",
    "extort", "kidnap", "traffick", "prostitute", "illegal", "sell organs", "assault",
    "arson", "embezzle",

    # 🤬 INSULTS / HATE / SLURS
    "idiot", "stupid", "dumb", "moron", "retard", "retarded", "loser", "fatass",
    "ugly", "bastard", "douche", "fuckface", "shitface", "asshole", "jerk", "motherfucker",
    "cunt", "fag", "faggot", "tranny", "nigger", "nigga", "kike", "chink", "spic",
    "wetback", "sandnigger", "towelhead", "gypsy", "coon", "gook", "paki", "whore",
    "hoe", "slut", "bitch", "dickhead", "gay", "die", "kill yourself",

    # 👿 RELIGIOUS / POLITICAL EXTREMISM
    "allah is", "kill infidels", "burn church", "bomb mosque", "convert or die",
    "zionist pig", "anti-semitic", "crusade", "jihad", "infidel", "heathen", "satanist",
    "nazi", "hitler", "kkk", "white power", "islamophobic", "homophobic", "god hates",
    "burn bible", "destroy quran",

    # 💩 OTHER OFFENSIVE / TROLLING
    "poop", "shit", "piss", "pee", "crap", "fart", "suck", "balls", "screw you",
    "hell", "damn", "goddamn", "wtf", "stfu", "kys", "lmao", "lmfao", "omfg",
    "nudes", "send nudes", "noob", "rekt", "loser", "trash", "garbage",

    # ⚙️ DARKNET / CYBERCRIME
    "tor", "darkweb", "deepweb", "0day", "exploit", "keylogger", "rootkit",
    "rat", "malware", "virus", "trojan", "payload", "ransomware", "ddos",
    "bruteforce", "hydra", "proxychain", "sqlmap", "credit card", "cc dump"
]

useragent = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.105 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.102 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.64 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.138 Safari/537.36",

    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.1; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",

    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6_8) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",

    # Edge (Chromium)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.105 Safari/537.36 Edg/119.0.2151.72",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36 Edg/117.0.2045.31",

    # Headless Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/119.0.6045.105 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/118.0.5993.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/117.0.5938.149 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/116.0.5845.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/115.0.5790.110 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/113.0.5672.64 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/112.0.5615.138 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/111.0.5563.64 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) HeadlessChrome/110.0.5481.100 Safari/537.36",

    # Bots (just in case you wanna sneak in one 👀)
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; DuckDuckBot/1.0; +http://duckduckgo.com/duckduckbot.html)",
    "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",

    # Python-based scrapers
    "python-requests/2.31.0",
    "Python/3.11 aiohttp/3.8.5",
    "Mozilla/5.0 (compatible; Scrapy/2.5.1; +https://scrapy.org)",
    "curl/8.1.2",
    "Wget/1.21.3",

    # Brave pretending to be Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.105 Safari/537.36 Brave/1.59.117"
]

ADMIN_CODE = "ICU14CU"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:10000")
if RENDER_URL.endswith('/'):
    RENDER_URL = RENDER_URL[:-1]
chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
chromedriver_bin = os.environ.get("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")

user_agent = random.choice(useragent)

options = Options()
options.binary_location = chrome_bin
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")

service = Service(chromedriver_bin)
driver = webdriver.Chrome(service=service, options=options)
logged_in = False

def login_once(email, password):
    global logged_in
    if not logged_in:
        login_to_bing(driver, email, password)
        logged_in = True


def prompt_blocker(prompt):
    prompt = prompt.lower()
    for word in bad_words:
        pattern = rf"\b{re.escape(word)}\b"
        if re.search(pattern, prompt):
            return word  # Return the first word it finds
    return None

def take_screenshot_in_memory(driver):
    try:
        logging.info("📸 Capturing full-page screenshot using CDP...")
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        width = metrics["contentSize"]["width"]
        height = metrics["contentSize"]["height"]
        
        # Set the viewport to full height
        driver.set_window_size(width, height)
        
        screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "fromSurface": True,
            "captureBeyondViewport": True
        })
        screenshot_png = base64.b64decode(screenshot_data["data"])
        return screenshot_png
    except Exception as e:
        logging.error(f"❌ Failed to capture full-page screenshot: {e}")
        raise



def login_to_bing(driver, email, password):
    try:
        logging.info("🔗 Navigating to Bing login page...")
        driver.get("https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3a%2f%2fwww.bing.com%2fimages%2fcreate%3fsude%3d1&cobrandid=03f1ec5e-1843-43e5-a2f6-e60a6e0b1b9b")
        time.sleep(3)
        logging.info("✅ Login page loaded.")
        take_screenshot_in_memory(driver)
        time.sleep(3)

        logging.info("📧 Entering email...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "usernameEntry")))
        driver.find_element(By.ID, "usernameEntry").send_keys(email)
        logging.info("✅ Email entered.")
        driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
        logging.info("🖱️ Clicked next after email.")
        time.sleep(3)
        take_screenshot_in_memory(driver)

        logging.info("🔑 Using password login...")
        try:
            use_pwd_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Use your password')]"))
            )
            use_pwd_btn.click()
            logging.info("🖱️ Clicked 'Use your password'.")
            time.sleep(2)
            take_screenshot_in_memory(driver)
        except TimeoutException:
            logging.info("'Use your password' button not found. Proceeding directly to password entry.")

        logging.info("🔒 Entering password...")
        driver.find_element(By.ID, "passwordEntry").send_keys(password)
        logging.info("✅ Password entered.")
        driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
        logging.info("🖱️ Clicked next after password.")
        time.sleep(5)

        # ✅ Attempt to bypass passkey screen if present
        logging.info("🔍 Checking for bypass passkey option...")
        try:
            bypass_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((
                    By.XPATH, "//button[contains(text(), 'Skip for now') or @data-test='skip-passkey' or @data-testid='skip-passkey']"
                ))
            )
            bypass_button.click()
            logging.info("✅ Bypassed passkey screen.")
            take_screenshot_in_memory(driver)
        except TimeoutException:
            logging.info("⏭️ No passkey screen detected, continuing login.")

        # ✅ Stay signed in
        logging.info("✅ Staying signed in...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='primaryButton']"))
        ).click()
        logging.info("🖱️ Clicked 'Stay signed in'.")

        logging.info("===Navigated To Main Page===")
        driver.get("https://bing.com/images/create")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "gi_form_q"))
        )
        take_screenshot_in_memory(driver)

    except Exception as e:
        logging.error(f"❌ Login failed: {e}")
        take_screenshot_in_memory(driver)
        raise

        
def generate_images(driver, prompt):
    try:
        # 🔄 Ensure we're on the correct page
        if "bing.com/images/create" not in driver.current_url:
            logging.warning("⚠️ Wrong page! Redirecting to Bing Create...")
            driver.get("https://www.bing.com/images/create")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "gi_form_q"))
            )

        # 🖊️ Type prompt
        logging.info("🖊️ Typing prompt...")
        textarea = driver.find_element(By.ID, "gi_form_q")
        textarea.clear()
        textarea.send_keys(prompt)
        logging.info("✅ Prompt typed!")

        # 🖱️ CLICK FIX: Scroll button into view and use JavaScript click
        logging.info("🖱️ Preparing to click 'Create'...")
        create_button = driver.find_element(By.ID, "create_btn_c")
        driver.execute_script("arguments[0].scrollIntoView(true);", create_button)  # Scroll to button
        time.sleep(1)  # Let scrolling complete
        driver.execute_script("arguments[0].click();", create_button)  # JS click bypasses overlay
        logging.info("🎯 Create button clicked!")
        take_screenshot_in_memory(driver)

        # ⏳ Wait for generation with timeout
        logging.info("⏳ Waiting for images...")
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.image-row-img"))
            )
            logging.info("🎉 Images generated!")
        except TimeoutException:
            logging.error("⌛ Timeout! Refreshing page...")
            driver.get("https://www.bing.com/images/create")
            raise RuntimeError("Image generation timed out")

        # 💾 Extract images
        logging.info("💾 Extracting images...")
        base64_images = driver.execute_async_script("""
            const done = arguments[0];
            const imgs = Array.from(document.querySelectorAll('img.image-row-img'));
            if (imgs.length === 0) return done({error: "No images found"});
            
            Promise.all(imgs.map(img => {
                return fetch(img.src)
                    .then(res => res.blob())
                    .then(blob => new Promise(resolve => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    }));
            })).then(done);
        """)

        if isinstance(base64_images, dict) and 'error' in base64_images:
            raise RuntimeError(base64_images['error'])

        # 🧹 Cleanup
        logging.info("🧹 Clearing prompt...")
        driver.find_element(By.ID, "sb_form_q").clear()
        logging.info("✨ Ready for next request!")

        return base64_images

    except Exception as e:
        logging.error(f"💥 ERROR: {str(e)}")
        take_screenshot_in_memory(driver)
        raise
def save_base64_images(base64_list):
    saved = []
    for data_url in base64_list:
        if not data_url.startswith("data:image"):
            continue
        _, base64_data = data_url.split(",", 1)
        img_data = base64.b64decode(base64_data)
        file_id = str(uuid.uuid4())
        path = os.path.join(TEMP_IMAGE_DIR, f"{file_id}.png")
        with open(path, "wb") as f:
            f.write(img_data)
        saved.append({"url": f"/serve-image/{file_id}"})
        logging.info(f"✅ Image saved: {path}")
    return saved

from threading import Lock

generation_lock = Lock()

@app.route("/api/gen", methods=["GET", "POST"])
def generate():
    if not generation_lock.acquire(blocking=False):
        return jsonify({"error": "Another image generation is in progress. Please wait."}), 429

    try:
        is_json = request.is_json and request.method == "POST"
        source = request.args if request.method == "GET" else (request.get_json() or {})

        api_key = source.get("api_key")
        if not api_key or api_key not in API_KEYS:
            return jsonify({"error": "Invalid or missing API key."}), 401

        prompt = source.get("prompt")
        if not prompt:
            return jsonify({"error": "Missing prompt."}), 400

        # ✳️ Check for bad words using regex + word list
        bad = prompt_blocker(prompt)
        if bad:
            return jsonify({
                "error": "Prompt rejected: contains offensive or harmful content.",
                "blocked_word": bad
            }), 400

        # ✅ Proceed with image generation
        base64_images = generate_images(driver, prompt)
        base64_images = list(dict.fromkeys(base64_images))[:4]
        saved = save_base64_images(base64_images)

        logging.info(f"✅ Generated and saved {len(saved)} images for prompt: {prompt}")
        return jsonify(saved)

    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    finally:
        generation_lock.release()


@app.route("/api/screenshot")
def serve_screenshot_api():
    try:
        screenshot_png = take_screenshot_in_memory(driver)
        logging.info("✅ Screenshot served as PNG.")
        return send_file(
            BytesIO(screenshot_png),
            mimetype="image/png",
            as_attachment=False,
            download_name="screenshot.png"
        )
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/serve-image/<image_id>")
def serve_image(image_id):
    path = os.path.join(TEMP_IMAGE_DIR, f"{image_id}.png")
    if not os.path.exists(path):
        return jsonify({"error": "Image not found"}), 404
    logging.info(f"✅ Serving image: {path}")
    return send_file(path, mimetype="image/png")

@app.route('/refresh', methods=['POST'])
def refresh_browser_only():
    """
    Refresh (restart) the browser instance, WITHOUT re-login.
    """
    global driver
    try:
        driver.quit()
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("✅ Browser has been refreshed (no relogin).")
        return jsonify({"status": "success", "message": "Browser refreshed (no relogin)."}), 200
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart_browser_and_relogin():
    """
    Restart the browser instance AND perform re-login.
    """
    global driver, email, password, logged_in
    try:
        driver.quit()
        driver = webdriver.Chrome(service=service, options=options)
        login_to_bing(driver, email, password)
        logged_in = True
        logging.info("✅ Browser has been restarted and re-logged in.")
        return jsonify({"status": "success", "message": "Browser restarted and re-logged in."}), 200
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/getkey")
def get_key():
    key = random.choice(API_KEYS)
    return jsonify({"api_key": key})

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error_message="Resource not found."), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("error.html", error_message="Method not allowed."), 405

@app.errorhandler(Exception)
def handle_exception(e):
    return render_template("error.html", error_message="An unexpected error occurred."), 500

def get_binary_version(binary_path):
    try:
        result = subprocess.run([binary_path, "--version"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Could not determine version: {e}"

if __name__ == '__main__':
    email = os.getenv("email")
    password = os.getenv("password")

    if not email or not password:
        print("❌ Missing email or password in .env file.")
        exit(1)

    print("🔍 Chromium version:", get_binary_version(chrome_bin))
    print("🔍 Chromedriver version:", get_binary_version(chromedriver_bin))

    try:
        login_to_bing(driver, email, password)
        logged_in = True
        print("✅ Logged in to Bing successfully.")
    except Exception as e:
        print("❌ Login failed:", e)
        exit(1)

    app.run(host='0.0.0.0', port=10000)
