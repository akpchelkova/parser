import re
from collections import Counter
from tkinter import Tk, Listbox, Button, MULTIPLE, END, Scrollbar, Label, messagebox, Text, Toplevel, Entry
import nltk
import vk_api
from nltk.corpus import stopwords
import praw

# Устанавливаем стоп-слова для предобработки текста (скачивается один раз)
nltk.download('stopwords')

# API данные и токен для ВКонтакте
access_token = 'vk1.a.mYpgUUbCtQf4nUhL7uOxwo-lMirQB_XU2qYExS71RnXEuKO7eART1sDKh-XOSxTRwn52Xkr9MisZFEdtZ-sdZAoBQ3OuZ-F0jGBHfi0cp-6L0dLihWhw-Vq96He0zB0IKtzwA2h3FV-z4X1fO7GbTj0QheXB5LQpO86IeA2ea15C7rGkCDeYvENLqQirnsmFx-kiQ9LOGCizx0dac9U2sQ'

# API данные для Reddit
reddit_client_id = 'XsA2JcLrj6_rUHb_DlIGQA'
reddit_client_secret = 'yjrmMp_zAboemDno-VM4rLmAHpCpxw'
reddit_user_agent = 'pchelka v1.0'

# Функция для получения ID группы по ее alias в ВКонтакте
def get_group_id(alias, token):
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        group_info = vk.groups.getById(group_id=alias)
        return group_info[0]['id']
    except vk_api.VkApiError as error:
        print(f"Ошибка при запросе к VK API: {error}")
        return None

# Получение постов из ВКонтакте
def get_vk_posts(group_id, token, count=100):
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        if group_id > 0:
            group_id = -group_id
        response = vk.wall.get(owner_id=group_id, count=count)
        posts = [post['text'] for post in response['items'] if 'text' in post and post['text'].strip()]
        return posts
    except vk_api.VkApiError as error:
        print(f"Ошибка при запросе к VK API: {error}")
        return None

# Сбор данных из ВКонтакте
def collect_vk_data(source_name, group_id, token):
    data = get_vk_posts(group_id, token)
    if data:
        all_text = ' '.join(data)
        print(f"Данные собраны с {source_name}")
        return all_text
    else:
        print(f"Не удалось собрать данные с {source_name}")
        return None

# Получение постов из Reddit
def get_reddit_posts(subreddit_name, count=100):
    try:
        reddit = praw.Reddit(client_id=reddit_client_id,
                             client_secret=reddit_client_secret,
                             user_agent=reddit_user_agent)
        subreddit = reddit.subreddit(subreddit_name)
        posts = [submission.title + ' ' + submission.selftext for submission in subreddit.hot(limit=count)]
        return posts
    except Exception as e:
        print(f"Ошибка при запросе к Reddit API: {e}")
        return None

# Сбор данных из Reddit
def collect_reddit_data(source_name, subreddit_name):
    data = get_reddit_posts(subreddit_name)
    if data:
        all_text = ' '.join(data)
        print(f"Данные собраны с {source_name}")
        return all_text
    else:
        print(f"Не удалось собрать данные с {source_name}")
        return None

# Предобработка текста
def preprocess_text(data):
    stop_words = set(stopwords.words('russian') + stopwords.words('english'))
    cleaned_data = re.sub(r'\W+', ' ', data.lower())
    words = [word for word in cleaned_data.split() if word not in stop_words and len(word) > 2]
    return words

# Анализ данных
def analyze_data(source_name, all_text, output_file):
    words = preprocess_text(all_text)
    word_counts = Counter(words)
    common_words = word_counts.most_common(20)  # Изменено на 20 слов

    with open(output_file, "a", encoding='utf-8') as f:
        f.write(f"### Топ-20 слов для {source_name} ###\n")
        for word, count in common_words:
            f.write(f"{word}: {count}\n")
    print(f"Топ-20 слов для {source_name}: {common_words}")

# Парсинг ВКонтакте
def vk_parser(selected_groups):
    group_ids = {alias: get_group_id(alias=alias, token=access_token) for alias in selected_groups}
    group_ids = {name: id for name, id in group_ids.items() if id is not None}

    output_file = "all_vk_data.txt"

    with open(output_file, "w", encoding='utf-8') as f:
        f.write("")

    for name, group_id in group_ids.items():
        all_text = collect_vk_data(name, group_id, access_token)
        if all_text:
            analyze_data(name, all_text, output_file)

# Парсинг Reddit
def reddit_parser(selected_subreddits):
    output_file = "all_reddit_data.txt"

    with open(output_file, "w", encoding='utf-8') as f:
        f.write("")

    for subreddit_name in selected_subreddits:
        all_text = collect_reddit_data(subreddit_name, subreddit_name)
        if all_text:
            analyze_data(subreddit_name, all_text, output_file)

# Функция обработки парсинга
def parse_data(vk_input, reddit_input):
    vk_groups = [group.strip() for group in vk_input.get().split(",") if group.strip()]
    reddit_subreddits = [subreddit.strip() for subreddit in reddit_input.get().split(",") if subreddit.strip()]

    if vk_groups:
        vk_parser(vk_groups)
    if reddit_subreddits:
        reddit_parser(reddit_subreddits)

    messagebox.showinfo("Парсинг завершен", "Данные успешно собраны!")

# GUI
def create_gui():
    root = Tk()
    root.title("Парсинг VK и Reddit")

    Label(root, text="Введите алиасы групп ВКонтакте (через запятую):").pack()
    vk_input = Entry(root, width=80)
    vk_input.pack()

    Label(root, text="Введите названия сабреддитов (через запятую):").pack()
    reddit_input = Entry(root, width=80)
    reddit_input.pack()

    parse_button = Button(root, text="Запустить парсинг", command=lambda: parse_data(vk_input, reddit_input))
    parse_button.pack()

    view_vk_button = Button(root, text="Показать данные VK", command=lambda: show_file_content("all_vk_data.txt"))
    view_vk_button.pack()

    view_reddit_button = Button(root, text="Показать данные Reddit", command=lambda: show_file_content("all_reddit_data.txt"))
    view_reddit_button.pack()

    root.mainloop()

# Отображение содержимого файла
def show_file_content(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = f.read()
            window = Toplevel()
            window.title(f"Содержимое {file_name}")
            text_area = Text(window, wrap='word', width=80, height=20)
            text_area.pack(expand=True, fill='both')
            text_area.insert(END, data)
            scrollbar = Scrollbar(window)
            scrollbar.pack(side='right', fill='y')
            text_area.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=text_area.yview)
    except FileNotFoundError:
        messagebox.showerror("Ошибка", f"Файл {file_name} не найден.")

if __name__ == '__main__':
    create_gui()
