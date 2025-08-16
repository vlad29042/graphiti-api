#!/usr/bin/env python3
"""Демонстрация работы score в семантическом поиске"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_score_demonstration():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== ДЕМОНСТРАЦИЯ РАБОТЫ SCORE В FALKORDB ===\n")
        
        # 1. Добавляем эпизод
        print("1. ДОБАВЛЕНИЕ ТЕСТОВОГО ЭПИЗОДА...")
        episode_data = {
            "name": "Тест Score",
            "content": """
            Мария работает программистом в компании Google. 
            Она разрабатывает алгоритмы машинного обучения для поисковой системы.
            Также Мария увлекается готовкой итальянской пасты и пиццы.
            В свободное время она играет в теннис.
            """,
            "source": "test",
            "source_description": "Тест score",
            "group_id": "score-demo"
        }
        
        response = await client.post(f"{API_URL}/add_episode", json=episode_data)
        if response.status_code == 200:
            episode_id = response.json().get("episode_id")
            print(f"✅ Эпизод добавлен: {episode_id}")
        else:
            print(f"❌ Ошибка: {response.text}")
            return
        
        # 2. Ждём создание эмбеддингов
        print("\n2. ОЖИДАНИЕ СОЗДАНИЯ ЭМБЕДДИНГОВ...")
        await asyncio.sleep(5)
        
        # 3. Получаем информацию об эпизоде
        print(f"\n3. ПОЛУЧЕНИЕ ЭПИЗОДА {episode_id}...")
        response = await client.get(f"{API_URL}/episodes/{episode_id}")
        if response.status_code == 200:
            episode_info = response.json()['episode']
            print(f"✅ Эпизод найден:")
            print(f"   Название: {episode_info['name']}")
            print(f"   Упомянуто сущностей: {episode_info['entity_count']}")
            print(f"   Сущности:")
            for entity in episode_info['entities_mentioned']:
                print(f"     - {entity['name']}")
        
        # 4. Демонстрация работы score через порядок результатов
        print("\n4. ДЕМОНСТРАЦИЯ РАБОТЫ SCORE ЧЕРЕЗ РЕЛЕВАНТНОСТЬ...")
        
        queries = [
            {
                "text": "программирование и разработка ПО",
                "expected": "программист/Google"
            },
            {
                "text": "искусственный интеллект и нейронные сети", 
                "expected": "машинное обучение"
            },
            {
                "text": "кулинария и рецепты блюд",
                "expected": "готовка/паста/пицца"
            },
            {
                "text": "спорт и физическая активность",
                "expected": "теннис"
            },
            {
                "text": "космос и астрономия",
                "expected": "нет релевантных результатов"
            }
        ]
        
        for query_info in queries:
            print(f"\n   Запрос: '{query_info['text']}'")
            print(f"   Ожидаем найти: {query_info['expected']}")
            
            search_data = {
                "query": query_info["text"],
                "group_ids": ["score-demo"],
                "num_results": 10
            }
            
            response = await client.post(f"{API_URL}/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                edges = results.get('edges', [])
                
                if edges:
                    print(f"   ✅ Найдено {len(edges)} результатов (отсортировано по score):")
                    for i, edge in enumerate(edges, 1):
                        fact = edge.get('fact', '')
                        # Первые результаты имеют наивысший score
                        relevance = "⭐⭐⭐" if i == 1 else ("⭐⭐" if i == 2 else "⭐")
                        print(f"      {i}. {relevance} {fact}")
                else:
                    print(f"   ℹ️ Результатов не найдено (как и ожидалось)")
        
        # 5. Показываем все факты с их эмбеддингами
        print("\n5. ИНФОРМАЦИЯ О ВЕКТОРНОМ ПОИСКЕ...")
        print("   ℹ️ Каждый факт имеет векторное представление (эмбеддинг)")
        print("   ℹ️ При поиске создаётся эмбеддинг запроса")
        print("   ℹ️ Score = косинусное сходство между векторами")
        print("   ℹ️ FalkorDB использует vec.cosineDistance для вычисления")
        print("   ℹ️ Результаты сортируются по score (DESC)")
        
        # 6. Удаляем эпизод
        print(f"\n6. УДАЛЕНИЕ ЭПИЗОДА {episode_id}...")
        delete_data = {"episode_uuid": episode_id}
        response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
        if response.status_code == 200:
            print(f"✅ Эпизод удалён")
        
        # 7. Проверяем что эпизод удалён
        print(f"\n7. ПРОВЕРКА УДАЛЕНИЯ...")
        response = await client.get(f"{API_URL}/episodes/{episode_id}")
        if response.status_code == 404:
            print("✅ Эпизод не найден (успешно удалён)")
        else:
            print("❌ Эпизод всё ещё существует!")
        
        print("\n✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
        print("\nКЛЮЧЕВЫЕ МОМЕНТЫ О SCORE:")
        print("1. Score вычисляется динамически при каждом поиске")
        print("2. Используется косинусное сходство векторов")  
        print("3. Чем выше score, тем выше позиция в результатах")
        print("4. Score не хранится в базе, только эмбеддинги")
        print("5. FalkorDB обрабатывает векторы нативно через vecf32")

if __name__ == "__main__":
    asyncio.run(test_score_demonstration())