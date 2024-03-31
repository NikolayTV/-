import unittest

def retrieve_article(retrieved_articles, article_id):
    """
    Функция для извлечения содержимого статьи по ее идентификатору из списка извлеченных статей.
    
    :param retrieved_articles: Список словарей, содержащих пути и содержимое статей.
    :param article_id: Идентификатор статьи для поиска.
    :return: Содержимое статьи, если найдено, иначе None.
    """
    for article in retrieved_articles:
        if article_id in article['path']:
            return article['content']
    return None

class TestRetrieveArticle(unittest.TestCase):
    def test_article_retrieval(self):
        # Пример извлеченных статей
        retrieved_articles = [
            {'path': 'Раздел II. Особенная часть > Глава 20. Административные правонарушения, посягающие на общественный порядок и общественную безопасность > Статья 20.3.3. Публичные действия, направленные на дискредитацию использования Вооруженных Сил Российской Федерации в целях защиты интересов Российской Федерации и ее граждан, поддержания международного мира и безопасности или исполнения государствен',
            'content': '1. Публичные действия, направленные...'},
            # Другие статьи
        ]
        
        # Идентификатор статьи, которую хотим найти
        article_id = "Статья 20.3.3."
        
        # Выполняем поиск
        content = retrieve_article(retrieved_articles, article_id)
        
        # Убедимся, что содержимое статьи было найдено
        self.assertIsNotNone(content, "Статья не была найдена.")
        
        # Можно добавить дополнительные проверки содержимого, если это необходимо

if __name__ == '__main__':
    unittest.main()
