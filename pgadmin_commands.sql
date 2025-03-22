
-- Создание таблицы
CREATE TABLE table_name (
    id SERIAL PRIMARY KEY,
    column1 VARCHAR(100),
    column2 INT,
    column3 DATE
);

-- Просмотр списка всех таблиц
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Вставка данных
INSERT INTO table_name (column1, column2, column3)
VALUES ('Text', 123, '2024-03-17');

-- Выборка данных
SELECT * FROM table_name;

-- Обновление данных
UPDATE table_name
SET column1 = 'New Value'
WHERE id = 1;

-- Удаление данных
DELETE FROM table_name
WHERE id = 1;

-- Удаление таблицы
DROP TABLE table_name;

-- Добавление нового столбца
ALTER TABLE table_name
ADD COLUMN new_column VARCHAR(50);

-- Удаление столбца
ALTER TABLE table_name
DROP COLUMN column_name;

-- Переименование таблицы
ALTER TABLE old_table_name
RENAME TO new_table_name;

-- Создание индекса
CREATE INDEX index_name
ON table_name (column_name);

-- Создание внешнего ключа
ALTER TABLE child_table
ADD CONSTRAINT fk_name FOREIGN KEY (column_name)
REFERENCES parent_table (id);

-- Фильтрация, сортировка, ограничение
SELECT * FROM table_name
WHERE column2 > 100
ORDER BY column3 DESC
LIMIT 10;

-- Агрегация
SELECT COUNT(*), AVG(column2), SUM(column2)
FROM table_name;

-- Создание базы данных и пользователя
CREATE DATABASE database_name;
CREATE USER username WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE database_name TO username;

-- Просмотр структуры таблицы
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'table_name';
