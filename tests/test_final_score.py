#!/usr/bin/env python3
"""Финальный тест - показываем score явно"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_final_score():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== ФИНАЛЬНЫЙ ТЕСТ: ЯВНОЕ ОТОБРАЖЕНИЕ SCORE ===\n")
        
        # 1. Добавляем эпизод
        print("1. ДОБАВЛЕНИЕ ЭПИЗОДА С РАЗНООБРАЗНЫМ СОДЕРЖАНИЕМ...")
        episode_data = {
            "name": "Финальный тест Score",
            "content": """
            Анна работает специалистом по искусственному интеллекту в компании DeepMind.
            Она занимается разработкой нейронных сетей для обработки естественного языка.
            Анна также преподаёт машинное обучение в университете.
            В выходные Анна любит кататься на велосипеде в парке.
            Она готовит вегетарианские блюда и увлекается йогой.
            """,
            "source": "test",
            "source_description": "Финальный тест",
            "group_id": "final-score"
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
        
        # 3. Получаем эпизод
        print(f"\n3. ПРОВЕРКА ЭПИЗОДА {episode_id}...")
        response = await client.get(f"{API_URL}/episodes/{episode_id}")
        if response.status_code == 200:
            episode_info = response.json()['episode']
            print(f"✅ Эпизод содержит {episode_info['entity_count']} сущностей")
            print("Сущности:")
            for entity in episode_info['entities_mentioned'][:5]:
                print(f"  - {entity['name']}")
            if len(episode_info['entities_mentioned']) > 5:
                print(f"  ... и ещё {len(episode_info['entities_mentioned']) - 5}")
        
        # 4. Обычный поиск (без score)
        print("\n4. ОБЫЧНЫЙ ПОИСК (score скрыт)...")
        search_data = {
            "query": "искусственный интеллект и нейронные сети",
            "group_ids": ["final-score"],
            "num_results": 5
        }
        
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"Найдено {len(edges)} результатов (отсортировано по score):")
            for i, edge in enumerate(edges, 1):
                print(f"  {i}. {edge.get('fact')}")
        
        # 5. Поиск с отображением score!
        print("\n5. ПОИСК С ЯВНЫМ ОТОБРАЖЕНИЕМ SCORE! 🎯")
        response = await client.post(f"{API_URL}/search_with_score", json=search_data)
        if response.status_code == 200:
            result = response.json()
            print(f"Запрос: '{result['query']}'")
            print(f"Найдено результатов: {result['results_count']}\n")
            
            print("РЕЗУЛЬТАТЫ С ОЦЕНКОЙ РЕЛЕВАНТНОСТИ:")
            print("-" * 80)
            for i, res in enumerate(result['results'], 1):
                print(f"{i}. Факт: {res['fact']}")
                print(f"   От: {res['source_entity']} → К: {res['target_entity']}")
                print(f"   SCORE: {res['score']:.4f} ({res['score_percent']})")
                print(f"   UUID: {res['uuid']}")
                print("-" * 80)
        else:
            print(f"❌ Ошибка: {response.text}")
        
        # 6. Тестируем с разными запросами
        print("\n6. ТЕСТИРОВАНИЕ SCORE С РАЗНЫМИ ЗАПРОСАМИ...")
        test_queries = [
            "машинное обучение и data science",
            "спорт и физическая активность", 
            "еда и кулинария",
            "космические исследования"  # Нерелевантный запрос
        ]
        
        for query in test_queries:
            print(f"\nЗапрос: '{query}'")
            search_data["query"] = query
            
            response = await client.post(f"{API_URL}/search_with_score", json=search_data)
            if response.status_code == 200:
                result = response.json()
                if result['results']:
                    top_result = result['results'][0]
                    print(f"  Топ результат: {top_result['fact']}")
                    print(f"  Score: {top_result['score']:.4f} ({top_result['score_percent']})")
                else:
                    print("  Релевантных результатов не найдено")
        
        # 7. Удаление и проверка
        print(f"\n7. УДАЛЕНИЕ ЭПИЗОДА {episode_id}...")
        delete_data = {"episode_uuid": episode_id}
        response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
        if response.status_code == 200:
            print("✅ Эпизод удалён")
        
        # Проверка удаления через поиск
        print("\n8. ПРОВЕРКА УДАЛЕНИЯ ЧЕРЕЗ ПОИСК...")
        response = await client.post(f"{API_URL}/search_with_score", json=search_data)
        if response.status_code == 200:
            result = response.json()
            if result['results_count'] == 0:
                print("✅ Данные успешно удалены - поиск не находит результатов")
            else:
                print(f"❌ Найдено {result['results_count']} результатов после удаления")
        
        print("\n✅ ФИНАЛЬНЫЙ ТЕСТ ЗАВЕРШЁН!")
        print("\n🎯 ВЫВОДЫ О SCORE:")
        print("1. Score - это косинусное сходство между векторами (0 до 1)")
        print("2. Чем ближе к 1, тем выше семантическая близость")
        print("3. FalkorDB вычисляет: (2 - vec.cosineDistance(v1, v2))/2")
        print("4. Порог отсечения обычно 0.5 (50%)")
        print("5. Результаты автоматически сортируются по score DESC")

if __name__ == "__main__":
    asyncio.run(test_final_score())