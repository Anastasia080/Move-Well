**Описание методов API**

**1.Аутентификация и профиль**

**POST /register – регистрация**

{

"email": "user@mail.ru",

"password": "secure123"

}

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "email": "string", "password": "string" } |
| Возвращает | { "user_id": "uuid", "access_token": "string", "refresh_token": "string" } |
| Описание | Создаёт нового пользователя в таблице users с указанными email и паролем. Возвращает идентификатор пользователя и токены для авторизации. |

**POST /login – вход**

{ "email": "user@mail.ru", "password": "secure123" }

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "email": "string", "password": "string" } |
| Возвращает | { "access_token": "string", "refresh_token": "string" } |
| Описание | Аутентификация. Обновляет last_login в таблице users. |

**POST /profile – заполнение профиля**

{

"profile": {

"age": 67,

"diagnosis": "arthrosis",

"mobility_limits": \["left_arm"\]

}

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "profile": { "age": "int", "diagnosis": "string", "mobility_limits": \["string"\] } } |
| Возвращает | { "user_id": "uuid", "email": "string", "profile": { ... } } |
| Описание | Заполняет профиль пользователя в таблице users после регистрации. Сохраняет возраст, диагноз и ограничения подвижности. |

**GET /profile – получить профиль**

{

"user_id": "uuid",

"email": "user@mail.ru",

"profile": {

"age": 67,

"diagnosis": "arthrosis",

"mobility_limits": \["left_arm"\]

}

}

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | – (только заголовок авторизации) |
| Возвращает | { "user_id": "uuid", "email": "string", "profile": { "age": "int", "diagnosis": "string", "mobility_limits": \["string"\] } } |
| Описание | Возвращает полные данные профиля текущего авторизованного пользователя. |

**PUT /profile – обновить профиль**

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "age": "int", "diagnosis": "string", "mobility_limits": \["string"\] }(одно или несколько полей) |
| Возвращает | { "user_id": "uuid", "email": "string", "profile": { ... } }(обновлённый профиль) |
| Описание | Частично или полностью обновляет данные профиля пользователя. |

**DELETE /profile – удалить аккаунт (с подтверждением)**

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "confirmation": "true" } или { "password": "string" } (для подтверждения) |
| Возвращает | 204 No Content (пустой ответ) |
| Описание | Безвозвратно удаляет учётную запись пользователя и все связанные данные (избранное и прогресс). Требует подтверждения. |

**2\. Упражнения (каталог, избранное)**

**GET /exercises – список всех упражнений**

\[

{

"id": "ex_001",

"title": "Подъём рук вверх",

"category": "arms",

"video_url": "...",

"duration_sec": 45,

"description": "...",

"key_points": \[...\],

"is_favorite": 0

}

\]

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | Query-параметры: category (arms/legs/body), search(строка поиска) – опционально |
| Возвращает | \[ { "id": "string", "title": "string", "category": "string", "video_url": "string", "duration_sec": "int", "description": "string", "key_points": \["string"\], "is_favorite": "boolean" } \] |
| Описание | Возвращает список всех упражнений с возможностью фильтрации по категории и поиска по названию. is_favorite вычисляется через EXISTS в таблице favorites для текущего пользователя. |

**GET /exercises/{id} – детали упражнения**

{

"id": "ex_001",

"title": "Подъём рук вверх",

"category": "arms",

"video_url": "...",

"duration_sec": 45,

"description": "...",

"key_points": \[...\],

"is_favorite": 0

}

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | id – идентификатор упражнения |
| Возвращает | { "id": "string", "title": "string", "category": "string", "video_url": "string", "duration_sec": "int", "description": "string", "key_points": \["string"\], "is_favorite": "boolean" } |
| Описание | Возвращает подробную информацию о конкретном упражнении по его ID. |

**POST /exercises/{id}/favorite – добавить в избранное**

{ "is_favorite": 1 }

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | id – идентификатор упражнения |
| Возвращает | { "is_favorite": 1, "message": "Упражнение добавлено в избранное" } |
| Описание | Добавляет указанное упражнение в список избранных для текущего пользователя – добавляет в таблицу favorites. |

**DELETE /exercises/{id}/favorite – удалить из избранного**

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | id – идентификатор упражнения в пути URL |
| Возвращает | 204 No Content (пустой ответ) |
| Описание | Удаляет указанное упражнение из списка избранных текущего пользователя. |

**GET /favorites – список избранных упражнений**

\[

{

"id": "ex_001",

"title": "Подъём рук вверх",

"category": "arms",

"video_url": "...",

"duration_sec": 45,

"description": "...",

"key_points": \[...\],

"is_favorite": 1

}

\]

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | – (только заголовок авторизации) |
| Возвращает | \[ { "id": "string", "title": "string", "category": "string", "video_url": "string", "duration_sec": "int", "description": "string", "key_points": \["string"\], "is_favorite": 1 } \] |
| Описание | Возвращает список всех упражнений, которые пользователь добавил в избранное. Поле is_favorite всегда равно 1. |

**3\. Прогресс выполнения**

**POST /progress – сохранить результат упражнения**

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | { "exercise_id": "string", "result": "success/errors", "errors": \["string"\], "duration_sec": "int" } |
| Возвращает | { "progress_id": "uuid", "created_at": "timestamp" } |
| Действие в БД | Создает запись в таблице progress |

**GET /progress/{progress_id} – получить обратную связь по выполнению**

|     |     |
| --- | --- |
| **Параметр** | **Описание** |
| Получает | progress_id – идентификатор записи в таблице progress |
| Возвращает | Объект с полной обратной связью (результат, ошибки) |
| Описание | Возвращает детальную обратную связь после выполнения упражнения. |