import time
import os
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class QuizAutomation:
    def __init__(self, quiz_url):
        print("[INFO] Initializing WebDriver...")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver.maximize_window()
        self.quiz_url = quiz_url
        self.learned_answers = self.load_answers()

    def load_answers(self):
        if os.path.exists("learned_answers.json"):
            with open("learned_answers.json", "r", encoding="utf-8") as f:
                all_answers = json.load(f)
            return all_answers.get(self.quiz_url, {})
        return {}

    def save_answers(self):
        print("[INFO] Saving learned answers to file...")
        all_answers = {}
        if os.path.exists("learned_answers.json"):
            with open("learned_answers.json", "r", encoding="utf-8") as f:
                all_answers = json.load(f)
        all_answers[self.quiz_url] = self.learned_answers
        with open("learned_answers.json", "w", encoding="utf-8") as f:
            json.dump(all_answers, f, ensure_ascii=False, indent=2)

    def open_url(self, url):
        print(f"[INFO] Opening URL: {url}")
        self.driver.get(url)
        time.sleep(1)

    def set_cookies(self, cookies):
        print("[INFO] Setting cookies...")
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        print("[SUCCESS] Cookies set.")

    def click_button(self, *texts):
        print(f"[INFO] Trying to click one of these buttons: {texts}")
        for text in texts:
            try:
                button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//button[contains(text(),'{text}')] | //a[contains(text(),'{text}')]"))
                )
                button.click()
                print(f"[SUCCESS] Clicked button: {text}")
                time.sleep(2)
                return
            except:
                continue
        print(f"[WARNING] Buttons {texts} not found.")

    def start_quiz(self):
        print("[INFO] Starting quiz...")
        time.sleep(1)
        self.click_button("Faire un autre essai")
        time.sleep(1)
        self.click_button("Démarrer le quiz")

    def answer_questions(self):
        print("[INFO] Answering questions one at a time...")
        question_elements = self.driver.find_elements(By.CSS_SELECTOR, ".quiz-item")
        if not question_elements:
            print("[WARNING] No questions found on the page!")
            return False

        for i, question_element in enumerate(question_elements):
            print(f"[INFO] Processing Question {i + 1}...")
            try:
                question_text = question_element.find_element(By.CSS_SELECTOR, ".question-title").text.strip()
                options = question_element.find_elements(By.CSS_SELECTOR, ".js-choices")
                option_texts = [option.text.strip() for option in options if option.text.strip()]
                if not option_texts:
                    print("[WARNING] No answer choices detected. Skipping.")
                    continue

                multiple_answers = "Plusieurs réponses sont possibles" in question_element.text

                if question_text in self.learned_answers:
                    correct_answers = self.learned_answers[question_text]
                    print(f"[INFO] Using learned answers: {correct_answers}")
                    for opt_text in correct_answers:
                        for option in options:
                            if opt_text.strip().lower() in option.text.strip().lower():
                                try:
                                    input_el = option.find_element(By.CSS_SELECTOR, "input")
                                    self.driver.execute_script("arguments[0].click();", input_el)
                                except:
                                    label_el = option.find_element(By.CSS_SELECTOR, "label")
                                    self.driver.execute_script("arguments[0].click();", label_el)
                else:
                    num_choices = random.randint(1, len(option_texts)) if multiple_answers else 1
                    chosen = random.sample(options, num_choices)
                    for option in chosen:
                        try:
                            input_el = option.find_element(By.CSS_SELECTOR, "input")
                            self.driver.execute_script("arguments[0].click();", input_el)
                        except:
                            label_el = option.find_element(By.CSS_SELECTOR, "label")
                            self.driver.execute_script("arguments[0].click();", label_el)
                        print(f"[ANSWERED] Selected random answer.")

            except Exception as e:
                print(f"[ERROR] Failed to process question: {str(e)}")
                continue
        return True

    def submit_answers(self):
        print("[INFO] Submitting answers...")
        self.click_button("Valider")
        self.click_button("Voir la correction")
        self.extract_correct_answers()

    def extract_correct_answers(self):
        print("[INFO] Extracting correct answers from correction page...")
        question_elements = self.driver.find_elements(By.CSS_SELECTOR, ".quiz-item")
        for element in question_elements:
            try:
                question_text = element.find_element(By.CSS_SELECTOR, ".question-title").text.strip()
                good_answers_elements = element.find_elements(By.CSS_SELECTOR, ".list-group-item-success")
                good_answers = [el.text.strip() for el in good_answers_elements if el.text.strip()]
                if good_answers:
                    self.learned_answers[question_text] = good_answers
                    print(f"[LEARNED] {question_text} => {good_answers}")
            except Exception as e:
                print(f"[ERROR] Failed to extract correct answer: {str(e)}")
        self.save_answers()

    def reached_goal_score(self):
        print("[INFO] Checking if goal score is reached...")
        try:
            score_div = self.driver.find_element(By.CSS_SELECTOR, ".progress-details")
            current_score = score_div.find_element(By.CSS_SELECTOR, ".current").text.strip()
            goal_score = score_div.find_element(By.CSS_SELECTOR, ".goal-percentage").text.strip()
            print(f"[INFO] Current score: {current_score}, Goal: {goal_score}")
            return current_score == goal_score
        except Exception as e:
            print(f"[WARNING] Could not determine score: {e}")
            return False

    def retry_quiz(self):
        print("[INFO] Retrying quiz...")
        if self.reached_goal_score():
            print("[SUCCESS] Goal score reached! Pausing for manual interaction.")
            self.learned_answers.clear()
            input("[PAUSED] Appuyez sur Entrée pour continuer...")
        else:
            self.click_button("Fermer")
            self.click_button("Faire un autre essai")
            self.start_quiz()

    def automate_quiz(self, cookies):
        print("[INFO] Automating the quiz...")
        self.open_url(self.quiz_url)
        self.set_cookies(cookies)
        self.driver.refresh()
        self.start_quiz()
        while True:
            answered_questions = self.answer_questions()
            if not answered_questions:
                print("[ERROR] No questions found. Retrying...")
                self.driver.refresh()
                time.sleep(2)
                self.start_quiz()
                continue
            self.submit_answers()
            print("[INFO] Reviewing incorrect answers...")
            self.retry_quiz()

        print("[INFO] Closing browser...")
        self.driver.quit()


if __name__ == "__main__":
    quiz_url = input("Entrez l'URL du quiz : ").strip()
    cookies = [
        {"name": "ci_session", "value": input("Entrez votre cookie ci_session : ").strip()},
        {"name": "csrf_cookie_name", "value": input("Entrez votre cookie csrf_cookie_name : ").strip()},
    ]

    bot = QuizAutomation(quiz_url)
    bot.automate_quiz(cookies)
