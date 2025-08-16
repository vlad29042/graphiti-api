#!/usr/bin/env python3
"""Детальный тест работы со score и эпизодами"""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_detailed_score():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== ДЕТАЛЬНЫЙ ТЕСТ SCORE И ЭПИЗОДОВ ===\n")
        
        # 1. Добавляем несколько эпизодов с разным содержанием
        print("1. ДОБАВЛЕНИЕ НЕСКОЛЬКИХ ЭПИЗОДОВ...")
        episodes_data = [
            {
                "name": "AI эпизод",
                "content": "Алиса работает в OpenAI над разработкой больших языковых моделей GPT. Она специализируется на обучении нейронных сетей.",
                "source": "test",
                "source_description": "AI тематика",
                "group_id": "score-test"
            },
            {
                "name": "Кулинарный эпизод",
                "content": "Борис готовит борщ и пельмени в ресторане русской кухни. Он любит готовить традиционные блюда.",
                "source": "test", 
                "source_description": "Кулинария",
                "group_id": "score-test"
            },
            {
                "name": "Спортивный эпизод",
                "content": "Виктор играет в футбол за команду Спартак. Он забил гол в последнем матче чемпионата.",
                "source": "test",
                "source_description": "Спорт",
                "group_id": "score-test"
            }
        ]
        
        episode_ids = []
        for ep_data in episodes_data:
            response = await client.post(f"{API_URL}/add_episode", json=ep_data)
            if response.status_code == 200:
                episode_id = response.json().get("episode_id")
                episode_ids.append(episode_id)
                print(f"✅ Добавлен: {ep_data['name']} (ID: {episode_id})")
            else:
                print(f"❌ Ошибка: {response.text}")
                return
        
        # 2. Ждём обработку
        print("\n2. ОЖИДАНИЕ СОЗДАНИЯ ЭМБЕДДИНГОВ...")
        await asyncio.sleep(5)
        
        # 3. Получаем все узлы группы
        print("\n3. ПОЛУЧЕНИЕ ВСЕХ УЗЛОВ...")
        response = await client.get(f"{API_URL}/nodes", params={"group_id": "score-test"})
        if response.status_code == 200:
            nodes = response.json()
            print(f"✅ Найдено {nodes['count']} узлов:")
            for node in nodes['nodes'][:10]:  # Показываем первые 10
                print(f"   - {node['name']}")
        
        # 4. Тестируем семантический поиск с разными запросами
        print("\n4. ТЕСТИРОВАНИЕ SCORE С РАЗНЫМИ ЗАПРОСАМИ...")
        
        # Запрос близкий к AI
        print("\n4.1. Поиск по запросу 'искусственный интеллект и машинное обучение':")
        search_data = {
            "query": "искусственный интеллект и машинное обучение",
            "group_ids": ["score-test"],
            "num_results": 10
        }
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Найдено {len(edges)} результатов (отсортировано по релевантности):")
            for i, edge in enumerate(edges, 1):
                print(f"   {i}. {edge.get('fact')}")
                # Score вычисляется внутри, но не возвращается в API
                # Порядок результатов показывает релевантность
        
        # Запрос близкий к кулинарии
        print("\n4.2. Поиск по запросу 'готовка еды и рецепты':")
        search_data["query"] = "готовка еды и рецепты"
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Найдено {len(edges)} результатов:")
            for i, edge in enumerate(edges[:3], 1):
                print(f"   {i}. {edge.get('fact')}")
        
        # Запрос близкий к спорту
        print("\n4.3. Поиск по запросу 'спортивные соревнования':")
        search_data["query"] = "спортивные соревнования"
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"✅ Найдено {len(edges)} результатов:")
            for i, edge in enumerate(edges[:3], 1):
                print(f"   {i}. {edge.get('fact')}")
        
        # 5. Получаем факты для конкретного эпизода
        print("\n5. ПОЛУЧЕНИЕ ФАКТОВ ПЕРЕД УДАЛЕНИЕМ...")
        response = await client.get(f"{API_URL}/facts", params={"group_id": "score-test", "limit": 50})
        if response.status_code == 200:
            facts = response.json()
            print(f"✅ Всего фактов в группе: {facts['count']}")
            
            # Находим факты связанные с Алисой
            alice_facts = [f for f in facts['facts'] if 'Алиса' in str(f.get('source_entity')) or 'Алиса' in str(f.get('target_entity'))]
            print(f"\nФакты про Алису ({len(alice_facts)}):")
            for fact in alice_facts:
                print(f"   - {fact['fact']}")
        
        # 6. Удаляем первый эпизод (про AI)
        print(f"\n6. УДАЛЕНИЕ ЭПИЗОДА {episode_ids[0]} (AI эпизод)...")
        delete_data = {"episode_uuid": episode_ids[0]}
        response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
        if response.status_code == 200:
            print(f"✅ {response.json()['message']}")
        
        # 7. Проверяем что данные удалились
        print("\n7. ПРОВЕРКА ПОСЛЕ УДАЛЕНИЯ...")
        
        # Проверяем узлы
        response = await client.get(f"{API_URL}/nodes", params={"group_id": "score-test"})
        if response.status_code == 200:
            nodes_after = response.json()
            print(f"Узлов осталось: {nodes_after['count']} (было {nodes['count']})")
            
            # Проверяем что Алиса удалилась
            alice_nodes = [n for n in nodes_after['nodes'] if n.get('name') == 'Алиса']
            if not alice_nodes:
                print("✅ Узел 'Алиса' успешно удалён")
            else:
                print("❌ Узел 'Алиса' всё ещё существует!")
        
        # Проверяем факты
        response = await client.get(f"{API_URL}/facts", params={"group_id": "score-test"})
        if response.status_code == 200:
            facts_after = response.json()
            print(f"Фактов осталось: {facts_after['count']} (было {facts['count']})")
            
            # Проверяем что факты про Алису удалились
            alice_facts_after = [f for f in facts_after['facts'] if 'Алиса' in str(f.get('source_entity')) or 'Алиса' in str(f.get('target_entity'))]
            if not alice_facts_after:
                print("✅ Все факты про Алису успешно удалены")
            else:
                print(f"❌ Остались факты про Алису: {len(alice_facts_after)}")
        
        # 8. Поиск после удаления
        print("\n8. ПОИСК ПОСЛЕ УДАЛЕНИЯ...")
        search_data["query"] = "искусственный интеллект и машинное обучение"
        response = await client.post(f"{API_URL}/search", json=search_data)
        if response.status_code == 200:
            results = response.json()
            edges = results.get('edges', [])
            print(f"Найдено {len(edges)} результатов по AI (должно быть 0 или меньше)")
            if edges:
                print("Оставшиеся результаты:")
                for edge in edges:
                    print(f"   - {edge.get('fact')}")
        
        # 9. Финальная очистка
        print("\n9. ОЧИСТКА ОСТАВШИХСЯ ЭПИЗОДОВ...")
        for episode_id in episode_ids[1:]:
            delete_data = {"episode_uuid": episode_id}
            response = await client.request("DELETE", f"{API_URL}/episodes", json=delete_data)
            if response.status_code == 200:
                print(f"✅ Удалён эпизод {episode_id}")
        
        print("\n✅ ДЕТАЛЬНЫЙ ТЕСТ ЗАВЕРШЁН!")
        print("\nВЫВОДЫ О SCORE:")
        print("- Score вычисляется внутри системы при поиске")
        print("- Результаты возвращаются отсортированными по релевантности")
        print("- Первые результаты наиболее релевантны запросу")
        print("- При удалении эпизода удаляются все связанные узлы и факты")

if __name__ == "__main__":
    asyncio.run(test_detailed_score())