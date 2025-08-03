from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
from config import settings

class FaissStore:
    def __init__(self):
        self.dim = settings.VECTOR_DIM
        # Ленивая загрузка модели
        self.model = None
        self.index_path = settings.FAISS_INDEX_PATH
        self.meta_path = settings.FAISS_META_PATH
        self.index = None
        self.texts = []

    def _load_model(self):
        """Загружает модель при первом использовании"""
        if self.model is None:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Ошибка загрузки SentenceTransformer: {e}")
                raise

    def build(self, texts):
        self._load_model()
        embeddings = self.model.encode(texts, show_progress_bar=True)
        self.index = faiss.IndexFlatL2(self.dim)
        self.index.add(np.array(embeddings, dtype='float32'))
        # Сохраняем тексты для последующего маппинга результатов
        with open(self.meta_path, 'wb') as f:
            pickle.dump(texts, f)
        faiss.write_index(self.index, self.index_path)

    def load(self):
        # Проверяем существование файлов
        if not os.path.exists(self.index_path) or not os.path.exists(self.meta_path):
            print(f"FAISS индекс не найден: {self.index_path}")
            self.texts = []
            return
            
        # Загружаем индекс и связанные с ним тексты
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, 'rb') as f:
                self.texts = pickle.load(f)
        except Exception as e:
            print(f"Ошибка загрузки FAISS индекса: {e}")
            self.texts = []

    def query(self, text, k=5):
        # Загружаем модель при первом использовании
        self._load_model()
        
        # Если индекс не загружен, возвращаем пустой результат
        if self.index is None or len(self.texts) == 0:
            return []
        
        # Поиск по эмбеддингу заданного текста
        emb = self.model.encode([text])
        D, I = self.index.search(np.array(emb, dtype='float32'), k)
        # Возвращаем список (текст, расстояние)
        return [(self.texts[i], float(D[0][j])) for j, i in enumerate(I[0])]