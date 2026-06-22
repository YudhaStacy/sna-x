from time import sleep
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException, # Tambahkan ini
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from typing import List, Set, Tuple
from selenium.webdriver.common.keys import Keys

# --- Impor Baru untuk Explicit Wait (Penting untuk Modal) ---
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By 


class Tweet:
    def __init__(
        self,
        card: WebDriver,
        driver: WebDriver,
        actions: ActionChains,
        scrape_poster_details=False,
    ) -> None:
        
        self.card = card
        self.driver = driver
        self.actions = actions
        self.error = False
        self.tweet: Tuple = None
        
        # --- Pengikisan Atribut Statis Awal ---
        try:
            self.user = card.find_element(
                "xpath", './/div[@data-testid="User-Name"]//span'
            ).text
        except NoSuchElementException:
            self.error = True
            self.user = "skip"

        try:
            self.handle = card.find_element(
                "xpath", './/span[contains(text(), "@")]'
            ).text
        except NoSuchElementException:
            self.error = True
            self.handle = "skip"

        # --- LOGIKA REFLYING TO (Termasuk Pengguna Tersembunyi) ---
        self.replying_to: Set[str] = set()
        view_people_link: WebDriver = None 
        
        # 1. Mengikis semua @username yang terlihat
        try:
            reply_elements = card.find_elements(
                "xpath",
                './/div[contains(text(), "Replying to")]/parent::div//span[contains(text(), "@")]'
            )
            # Filter hanya yang benar-benar handle (dimulai dengan @)
            self.replying_to.update({u.text for u in reply_elements if u.text.startswith('@')})
        except NoSuchElementException:
            pass
            
        # 2. Mencari tautan "View people in conversation"
        try:
            view_people_link = card.find_element(
                "xpath",
                './/div[contains(text(), "Replying to")]/parent::div//a[@aria-label="View people in conversation"]'
            )
        except NoSuchElementException:
            pass
            
        # 3. Pengecekan Eksplisit: Jika tautan ditemukan, panggil _scrape_conversation_users
        if view_people_link is not None:
            # PANGGIL FUNGSI: Klik tautan dan kikis pengguna dari modal
            new_users = self._scrape_conversation_users(view_people_link)
            
            # Gabungkan username baru ke set untuk menghilangkan duplikat
            self.replying_to.update(new_users)
                
        # Konversi set (replying_to) ke list untuk output akhir
        self.replying_to = list(self.replying_to)
            
        # --- Pengikisan Atribut Statis Lanjutan ---
        
        try:
            self.date_time = card.find_element("xpath", ".//time").get_attribute(
                "datetime"
            )
            if self.date_time is not None:
                self.is_ad = False
        except NoSuchElementException:
            self.is_ad = True
            self.error = True
            self.date_time = "skip"

        if self.error:
            return

        try:
            card.find_element(
                "xpath", './/*[local-name()="svg" and @data-testid="icon-verified"]'
            )
            self.verified = True
        except NoSuchElementException:
            self.verified = False

        self.content = ""
        contents = card.find_elements(
            "xpath",
            '(.//div[@data-testid="tweetText"])[1]/span | (.//div[@data-testid="tweetText"])[1]/a',
        )

        for content in contents:
            self.content += content.text

        try:
            self.reply_cnt = card.find_element(
                "xpath", './/button[@data-testid="reply"]//span'
            ).text
            if self.reply_cnt == "":
                self.reply_cnt = "0"
        except NoSuchElementException:
            self.reply_cnt = "0"

        try:
            self.retweet_cnt = card.find_element(
                "xpath", './/button[@data-testid="retweet"]//span'
            ).text
            if self.retweet_cnt == "":
                self.retweet_cnt = "0"
        except NoSuchElementException:
            self.retweet_cnt = "0"

        try:
            self.like_cnt = card.find_element(
                "xpath", './/button[@data-testid="like"]//span'
            ).text
            if self.like_cnt == "":
                self.like_cnt = "0"
        except NoSuchElementException:
            self.like_cnt = "0"

        try:
            self.analytics_cnt = card.find_element(
                "xpath", './/a[contains(@href, "/analytics")]//span'
            ).text
            if self.analytics_cnt == "":
                self.analytics_cnt = "0"
        except NoSuchElementException:
            self.analytics_cnt = "0"

        try:
            self.tags = card.find_elements(
                "xpath",
                './/a[contains(@href, "src=hashtag_click")]',
            )
            self.tags = [tag.text for tag in self.tags]
        except NoSuchElementException:
            self.tags = []

        try:
            self.mentions = card.find_elements(
                "xpath",
                '(.//div[@data-testid="tweetText"])[1]//a[contains(text(), "@")]',
            )
            self.mentions = [mention.text for mention in self.mentions]
        except NoSuchElementException:
            self.mentions = []

        try:
            raw_emojis = card.find_elements(
                "xpath",
                '(.//div[@data-testid="tweetText"])[1]/img[contains(@src, "emoji")]',
            )
            self.emojis = [
                emoji.get_attribute("alt").encode("unicode-escape").decode("ASCII")
                for emoji in raw_emojis
            ]
        except NoSuchElementException:
            self.emojis = []

        try:
            self.profile_img = card.find_element(
                "xpath", './/div[@data-testid="Tweet-User-Avatar"]//img'
            ).get_attribute("src")
        except NoSuchElementException:
            self.profile_img = ""

        try:
            self.tweet_link = self.card.find_element(
                "xpath",
                ".//a[contains(@href, '/status/')]",
            ).get_attribute("href")
            self.tweet_id = str(self.tweet_link.split("/")[-1])
        except NoSuchElementException:
            self.tweet_link = ""
            self.tweet_id = ""

        # --- Pengikisan Detail Poster ( scrape_poster_details=True ) ---
        self.following_cnt = "0"
        self.followers_cnt = "0"
        self.user_id = None
        
        if scrape_poster_details:
            # --- Logika Hover Card ---
            try:
                el_name = card.find_element(
                    "xpath", './/div[@data-testid="User-Name"]//span'
                )
            except NoSuchElementException:
                return
            
            ext_hover_card = False
            ext_user_id = False
            ext_following = False
            ext_followers = False
            hover_attempt = 0

            while (
                not ext_hover_card
                or not ext_user_id
                or not ext_following
                or not ext_followers
            ):
                try:
                    self.actions.move_to_element(el_name).perform()

                    hover_card = driver.find_element(
                        "xpath", '//div[@data-testid="hoverCardParent"]'
                    )

                    ext_hover_card = True

                    while not ext_user_id:
                        try:
                            raw_user_id = hover_card.find_element(
                                "xpath",
                                '(.//div[contains(@data-testid, "-follow")]) | (.//div[contains(@data-testid, "-unfollow")])',
                            ).get_attribute("data-testid")

                            if raw_user_id == "":
                                self.user_id = None
                            else:
                                self.user_id = str(raw_user_id.split("-")[0])

                            ext_user_id = True
                        except NoSuchElementException:
                            continue
                        except StaleElementReferenceException:
                            self.error = True
                            return

                    while not ext_following:
                        try:
                            self.following_cnt = hover_card.find_element(
                                "xpath", './/a[contains(@href, "/following")]//span'
                            ).text

                            if self.following_cnt == "":
                                self.following_cnt = "0"

                            ext_following = True
                        except NoSuchElementException:
                            continue
                        except StaleElementReferenceException:
                            self.error = True
                            return

                    while not ext_followers:
                        try:
                            self.followers_cnt = hover_card.find_element(
                                "xpath",
                                './/a[contains(@href, "/verified_followers")]//span',
                            ).text

                            if self.followers_cnt == "":
                                self.followers_cnt = "0"

                            ext_followers = True
                        except NoSuchElementException:
                            continue
                        except StaleElementReferenceException:
                            self.error = True
                            return
                except NoSuchElementException:
                    if hover_attempt == 3:
                        self.error = True
                        return
                    hover_attempt += 1
                    sleep(0.5)
                    continue
                except StaleElementReferenceException:
                    self.error = True
                    return

            if ext_hover_card and ext_following and ext_followers:
                # Reset actions setelah hover selesai
                self.actions.reset_actions()
                
        # --- Pembentukan Tuple Tweet Akhir ---
        self.tweet = (
            self.user,
            self.handle,
            self.date_time,
            self.verified,
            self.content,
            self.reply_cnt,
            self.retweet_cnt,
            self.like_cnt,
            self.analytics_cnt,
            self.tags,
            self.mentions,
            self.emojis,
            self.profile_img,
            self.tweet_link,
            self.tweet_id,
            self.user_id,
            self.following_cnt,
            self.followers_cnt,
            self.replying_to, # Menampilkan list username yang dibalas
        )
        pass

    def _scrape_conversation_users(self, view_people_link: WebDriver) -> List[str]:
        """
        Mengklik tautan 'View people in conversation' dan mengikis semua username 
        dari modal yang muncul menggunakan JavaScript Executor, dan menggunakan 
        explicit wait untuk stabilitas.
        """
        extra_users = []
        # XPATH untuk modal container (biasanya elemen teratas dengan role dialog)
        MODAL_CONTAINER_XPATH = '//div[@aria-labelledby="modal-header"]'
        # XPATH untuk username di dalam modal
        MODAL_USER_XPATH = './/div[@aria-labelledby="modal-header"]//span[contains(text(), "@")]'
        # XPATH untuk tombol tutup
        MODAL_CLOSE_BUTTON_XPATH = './/div[@aria-labelledby="modal-header"]//button[@aria-label="Close"]'

        # Simpan URL saat ini untuk mengatasi jika navigasi terjadi secara tidak sengaja
        current_url = self.driver.current_url
        
        try:
            # 1. Klik tautan untuk membuka modal menggunakan JavaScript
            self.driver.execute_script("arguments[0].click();", view_people_link)
            
            # 2. Tunggu modal dimuat (sampai kontainer dialog muncul)
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, MODAL_CONTAINER_XPATH))
            )

            # 3. Mengikis username dari modal
            # Tambahkan waktu tunggu singkat setelah modal muncul untuk memastikan konten dimuat
            sleep(1) 
            username_elements = self.driver.find_elements("xpath", MODAL_USER_XPATH)
            
            # Hanya ambil teks yang dimulai dengan '@'
            unique_users = {u.text for u in username_elements if u.text.startswith('@')}
            extra_users = list(unique_users)

            # 4. Menutup modal
            try:
                # Cobalah klik tombol tutup di dalam modal
                close_button = self.driver.find_element("xpath", MODAL_CLOSE_BUTTON_XPATH)
                close_button.click()
                # Tunggu hingga modal hilang
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, MODAL_CONTAINER_XPATH))
                )
            except (NoSuchElementException, TimeoutException):
                # Jika tombol tutup tidak ditemukan atau gagal, gunakan ESC
                # print("Peringatan: Mencoba menutup modal dengan ESC.")
                self.actions.send_keys(Keys.ESCAPE).perform()
                sleep(0.5)
            
        except TimeoutException:
            # print("Peringatan: Modal percakapan tidak muncul dalam waktu yang diharapkan.")
            pass
        except NoSuchElementException:
            # print("Peringatan: Gagal menemukan elemen username di modal.")
            pass
        except StaleElementReferenceException:
            # Pass, ini wajar jika DOM berubah cepat
            pass
        except Exception as e:
            # print(f"Terjadi kesalahan tak terduga saat pengikisan percakapan: {e}")
            pass
            
        # Pengecekan keamanan: Pastikan driver kembali ke URL yang benar setelah modal ditutup
        if self.driver.current_url != current_url:
            self.driver.get(current_url)
            sleep(2)
            
        return extra_users
