# Руководство Пользователя: Простой Чат Мессенджер

Это руководство поможет вам начать использовать приложение "Простой Чат Мессенджер".

## 1. Запуск Приложения

После запуска `client.py` вы увидите окно авторизации:

![Окно авторизации](https://github.com/user-attachments/assets/d976b47f-84ff-47b3-9244-f5c6fadd3135)


## 2. Регистрация Нового Пользователя

1.  Введите желаемое **Имя пользователя** в соответствующее поле.
2.  Введите **Пароль** в поле пароля.
3.  Нажмите кнопку **"Зарегистрироваться"**.
4.  Если регистрация успешна, вы увидите сообщение "Регистрация прошла успешно! Теперь вы можете войти." в окне терминала клиента и в самом окне чата (после входа).
5.  В случае, если имя пользователя уже занято, вы получите соответствующее сообщение.

## 3. Вход в Систему

1.  Введите ваше **Имя пользователя** и **Пароль**.
2.  Нажмите кнопку **"Войти"**.
3.  При успешном входе интерфейс изменится на главное окно чата.

## 4. Интерфейс Чата

После входа вы увидите основной интерфейс чата:

![Основной Интерфейс Чата](https://via.placeholder.com/800x600?text=Основной+Интерфейс+Чата)
*(Замените на скриншот вашего основного интерфейса чата)*

Интерфейс состоит из нескольких основных элементов:

* **Вкладки чатов (слева)**: Позволяют переключаться между "Общим Чатом", "Новым Чатом / Поиском" и вашими личными чатами.
* **Область сообщений (центр)**: Отображает историю сообщений для выбранной вкладки.
* **Поле ввода сообщения (внизу)**: Используется для набора и отправки сообщений.
* **Кнопка "Отправить"**: Отправляет введенное сообщение.

### 4.1. Общий Чат

Вкладка "Общий Чат" предназначена для публичных сообщений, которые видны всем подключенным пользователям.

* Выберите вкладку "Общий Чат".
* Введите ваше сообщение в поле ввода внизу.
* Нажмите "Отправить" или клавишу `Enter`.
* Ваше сообщение появится в истории чата у всех пользователей, включая вас. Также вы будете видеть системные сообщения о подключении/отключении пользователей.

### 4.2. Начать Новый Чат / Поиск Пользователей

Вкладка "Новый Чат / Поиск" позволяет найти других зарегистрированных пользователей и начать с ними личный чат.

1.  Выберите вкладку "Новый Чат / Поиск".
2.  Введите часть имени пользователя в поле поиска. Список ниже будет автоматически фильтроваться.
3.  Выберите пользователя из списка, кликнув по его имени.
4.  Автоматически откроется новая вкладка с личным чатом для выбранного пользователя, и вы сможете сразу начать общение.
5.  Кнопка "Обновить список пользователей" позволяет обновить список всех зарегистрированных пользователей, если кто-то новый зарегистрировался после вашего входа.

### 4.3. Личные Сообщения

Каждый личный чат отображается в отдельной вкладке, названной по имени вашего собеседника.

* Выберите вкладку нужного личного чата.
* Введите ваше сообщение в поле ввода внизу.
* Нажмите "Отправить" или клавишу `Enter`.
* Сообщения в личном чате видны только вам и вашему собеседнику.
* История сообщений с этим пользователем будет загружена автоматически при открытии вкладки.
* Кнопка "X" в правом верхнем углу вкладки личного чата позволяет закрыть ее. Закрытие вкладки *не удаляет* историю сообщений, вы сможете снова открыть чат с этим пользователем позже.

## 5. Отключение от Сервера

Чтобы отключиться от сервера и вернуться к экрану авторизации, нажмите кнопку **"Отключиться"** внизу главного окна чата.

## 6. Закрытие Приложения

Для полного закрытия приложения просто закройте окно чата. Если вы были подключены, приложение автоматически отключится от сервера.

---
