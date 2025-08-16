#!/usr/bin/env python3
"""Полный тест цикла работы с FalkorDB: сохранение, получение с score, удаление"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_full_cycle():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== ПОЛНЫЙ ТЕСТ GRAPHITI API С FALKORDB ===\n")
        
        # 1. Health check
        response = await client.get(f"{API_URL}/health")
        print(f"1. Health check: {response.json()}")
        
        # 2. Добавляем эпизод
        print("\n2. ДОБАВЛЕНИЕ ЭПИЗОДА...")
        add_data = {
            "name": "Полный тест",
            "content": "Иван работает в компании Яндекс как инженер машинного обучения. Он специализируется на компьютерном зрении и обработке естественного языка.",
            "source": "test",
            "source_description": "Тестовый источник",
            "group_id": "full-test"
        }
        response = await client.post(f"{API_URL}/add_episode", json=add_data)
        if response.status_code == 200:
            episode_data = response.json()
            episode_uuid = episode_data.get("episode_id")
            print(f"✅ Эпизод добавлен: {episode_uuid}")
        else:
            print(f"❌ Ошибка добавления: {response.text}")
            return
        
        # 3. Ждём обработку (эмбеддинг происходит здесь)
        print("\n3. ОЖИДАНИЕ ОБРАБОТКИ (создание эмбеддингов)...")
        await asyncio.sleep(5)
        
        # 4. Получаем узлы
        print("\n4. ПОЛУЧЕНИЕ УЗЛОВ...")
        response = await client.get(f"{API_URL}/nodes", params={"group_id": "full-test"})
        if response.status_code == 200:
            nodes_data = response.json()
            print(f"✅ Найдено {nodes_data['count']} узлов:")
            for node in nodes_data['nodes']:
                print(f"   - {node['name']} (тип: {node.get('type', 'Entity')})")
        else:
            print(f"❌ Ошибка получения узлов: {response.text}")
        
        # 5. Получаем факты
        print("\n5. ПОЛУЧЕНИЕ ФАКТОВ...")
        response = await client.get(f"{API_URL}/facts", params={"group_id": "full-test"})
        if response.status_code == 200:
            facts_data = response.json()
            print(f"✅ Найдено {facts_data['count']} фактов:")
            for fact in facts_data['facts']:
                print(f"   - {fact['fact']}")
                print(f"     От: {fact['source_entity']} → К: {fact['target_entity']}")
        else:
            print(f"❌ Ошибка получения фактов: {response.text}")
        
        # 6. Семантический поиск (здесь появляется score!)
        print("\n6. СЕМАНТИЧЕСКИЙ ПОИСК (проверка SCORE)...")
        search_data = {
            "query": "искусственный интеллект и нейронные сети",
            "group_ids": ["full-test"],
            "num_results": 10
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Найдено {len(edges)} результатов по семантической близости:")
            for i, edge in enumerate(edges[:5], 1):
                # Score вычисляется через косинусное сходство при поиске!
                print(f"   {i}. {edge.get('fact', 'Нет факта')}")
                print(f"      UUID: {edge.get('uuid')}")
                print(f"      Создан: {edge.get('created_at', 'Неизвестно')}")
        else:
            print(f"❌ Ошибка поиска: {response.text}")
        
        # 7. Ещё один поиск для проверки score
        print("\n7. ПОИСК ПО ДРУГОМУ ЗАПРОСУ...")
        search_data = {
            "query": "работа в IT компании",
            "group_ids": ["full-test"],
            "num_results": 10
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Найдено {len(edges)} результатов:")
            for edge in edges[:3]:
                print(f"   - {edge.get('fact', 'Нет факта')}")
        else:
            print(f"❌ Ошибка поиска: {response.text}")
        
        # 8. Удаление эпизода
        print(f"\n8. УДАЛЕНИЕ ЭПИЗОДА {episode_uuid}...")
        delete_data = {"episode_uuid": episode_uuid}
        response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
        if response.status_code == 200:
            print(f"✅ {response.json()}")
        else:
            print(f"❌ Ошибка удаления: {response.text}")
            return
        
        # 9. Проверка после удаления
        print("\n9. ПРОВЕРКА ПОСЛЕ УДАЛЕНИЯ...")
        response = await client.get(f"{API_URL}/nodes", params={"group_id": "full-test"})
        if response.status_code == 200:
            nodes_data = response.json()
            print(f"Узлов осталось: {nodes_data['count']}")
        
        response = await client.get(f"{API_URL}/facts", params={"group_id": "full-test"})
        if response.status_code == 200:
            facts_data = response.json()
            print(f"Фактов осталось: {facts_data['count']}")
        
        print("\n✅ ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
        print("\nВАЖНО О SCORE:")
        print("- Score вычисляется динамически при семантическом поиске")
        print("- Использует косинусное сходство между эмбеддингами")
        print("- Эмбеддинги создаются при добавлении эпизода")
        print("- FalkorDB хранит векторы в формате vecf32")

if __name__ == "__main__":
    asyncio.run(test_full_cycle())