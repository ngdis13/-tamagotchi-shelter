#!/bin/bash

echo "Запуск тестов nginx"
echo ""

# 1. Тест редиректа с HTTP на HTTPS
echo "1. Проверка автоматического редиректа HTTP -> HTTPS:"
curl -I http://localhost 2>&1 | grep -E "HTTP/|Location"
echo "-----------------------"
echo ""

# 2. Тест балансировки API (наш прошлый рабочий тест)
echo "2. Проверка балансировки бэкендов:"
for i in {1..4}
do
   curl -k -s https://localhost/api/pets | grep -o '"instance":"[^"]*"'
done
echo "-----------------------"
echo ""

# 3. Тест закрытой админки без пароля (ожидаем 401 Unauthorized)
echo "3. Проверка защиты /admin без авторизации (ожидаем 401):"
curl -k -I https://localhost/admin 2>&1 | grep "HTTP/"
echo "-----------------------"
echo ""

# 4. Тест закрытой админки с правильным паролем
echo "4. Проверка входа в /admin с паролем admin:supersecret:"
curl -k -u admin:supersecret https://localhost/admin
echo -e "\n-----------------------"
echo ""

# 5. Тест кастомного пути Alias (/docs -> info.txt)
echo "5. Проверка работы пути /docs (Alias):"
curl -k -s https://localhost/docs/
echo -e "\n-----------------------"
echo ""

# 6. Тест Rate Limit флуда (шлем 6 запросов подряд, должны посыпаться коды 429)
echo "6. Проверка защиты от флуда (Rate Limit, ожидаем появление кодов 429):"
for i in {1..6}
do
   curl -k -s -o /dev/null -w "%{http_code} " https://localhost/api/pets
done
echo -e "\n-----------------------"
echo ""

echo "Все тесты готовы! Устраиваем дэнс"
