import time
import os
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
        self.learned_answers = {}

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
                time.sleep(1)
                return True
            except:
                continue
        print(f"[WARNING] Buttons {texts} not found.")
        return False

    def click_next_quiz_link(self):
        print("[INFO] Searching for next quiz link...")
        try:
            while True:
                next_link = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.nav-bottom-next"))
                )
                classes = next_link.get_attribute("class")
                if "disabled" in classes:
                    print("[INFO] 'Suivant' button is disabled. Stopping.")
                    if "Evaluez votre niveau de compréhension" in self.driver.page_source:
                        print("[INFO] Found rating survey. Filling it...")
                        surveys = self.driver.find_elements(By.CSS_SELECTOR, "li.js-survey")
                        for survey in surveys:
                            stars = survey.find_elements(By.CSS_SELECTOR, ".js-star-score")
                            random.choice(stars).click()
                        self.click_button("Valider")
                        time.sleep(1)
                        return self.click_next_quiz_link()
                    return False
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", next_link)
                print("[SUCCESS] Clicked next quiz link.")
                time.sleep(2)
        except Exception as e:
            print(f"[WARNING] Failed to click next quiz link: {e}")
            return False

    def start_quiz(self):
        print("[INFO] Starting quiz...")
        time.sleep(0.5)
        self.click_button("Faire un autre essai")
        time.sleep(0.5)
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
                # Fill in the blanks
                fill_ins = question_element.find_elements(By.CSS_SELECTOR, "input.js-fills")
                for fill in fill_ins:
                    value = random.choice(["temporaire", "défini", "objectif", "unique"])
                    fill.clear()
                    fill.send_keys(value)
                    print(f"[ANSWERED] Filled input with: {value}")

                # Vrai / Faux
                true_false = question_element.find_elements(By.CSS_SELECTOR, ".btn-group[role='group']")
                for group in true_false:
                    choices = group.find_elements(By.CSS_SELECTOR, "label")
                    if choices:
                        choice = random.choice(choices)
                        self.driver.execute_script("arguments[0].click();", choice)
                        print(f"[ANSWERED] Selected: {choice.text.strip()}")

                # Choix multiples / simples
                options = question_element.find_elements(By.CSS_SELECTOR, ".js-choices")
                option_texts = [option.text.strip() for option in options if option.text.strip()]
                if option_texts:
                    multiple_answers = "Plusieurs réponses sont possibles" in question_element.text

                    if question_text := question_element.find_element(By.CSS_SELECTOR, ".question-title").text.strip():
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

    def reached_goal_score(self):
        print("[INFO] Checking if goal score is reached...")
        try:
            score_div = self.driver.find_element(By.CSS_SELECTOR, ".progress-details")
            current_score = int(score_div.find_element(By.CSS_SELECTOR, ".current").text.strip().replace('%', ''))
            goal_score = int(score_div.find_element(By.CSS_SELECTOR, ".goal-percentage").text.strip().replace('%', ''))
            print(f"[INFO] Current score: {current_score}%, Goal: {goal_score}%")
            return current_score >= goal_score
        except Exception as e:
            print(f"[WARNING] Could not determine score: {e}")
            return False

    def retry_quiz(self):
        print("[INFO] Retrying quiz...")
        if self.reached_goal_score():
            print("[SUCCESS] Goal score reached! Searching for next quiz...")
            self.learned_answers.clear()
            while not self.click_next_quiz_link():
                if self.click_button("Démarrer le quiz"):
                    print("[INFO] Next quiz found and started.")
                    return
                time.sleep(1)
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
        self.click_next_quiz_link()
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
    ]

    bot = QuizAutomation(quiz_url)
    bot.automate_quiz(cookies)
