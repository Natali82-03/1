# Импорт необходимых библиотек
import streamlit as st  # Для создания веб-интерфейса
import pandas as pd  # Для работы с данными
import matplotlib.pyplot as plt  # Для построения графиков
import matplotlib.colors as mcolors  # Для цветов в графиках
import chardet  # Для автоматического определения кодировки файлов

# Функция для загрузки данных с обработкой различных кодировок
@st.cache_data  # Декоратор для кэширования данных и ускорения работы
def load_data(file_name):
    """
    Загружает CSV-файл с автоматическим определением кодировки.
    Пробует несколько вариантов кодировок, если автоматическое определение не срабатывает.
    
    Параметры:
        file_name (str): Имя файла для загрузки
        
    Возвращает:
        pd.DataFrame: Загруженные данные
    """
    # Шаг 1: Пытаемся определить кодировку автоматически
    with open(file_name, 'rb') as f:
        rawdata = f.read(10000)  # Читаем первые 10КБ для анализа
        result = chardet.detect(rawdata)  # Определяем кодировку
    
    # Шаг 2: Пробуем загрузить с определенной кодировкой
    try:
        df = pd.read_csv(file_name, sep=';', encoding=result['encoding'])
    except UnicodeDecodeError:
        # Если автоматическое определение не сработало, пробуем ручные варианты
        try:
            # Попытка с UTF-8 (современный стандарт)
            df = pd.read_csv(file_name, sep=';', encoding='utf-8')
        except:
            try:
                # Попытка с Windows-1251 (для кириллицы)
                df = pd.read_csv(file_name, sep=';', encoding='cp1251')
            except:
                # Последний вариант - latin1 (редко, но читает почти всё)
                df = pd.read_csv(file_name, sep=';', encoding='latin1')
    
    # Шаг 3: Очистка данных после загрузки
    # Удаляем лишние пробелы в названиях столбцов
    df = df.rename(columns=lambda x: x.strip())
    
    # Проверяем наличие обязательного столбца с названиями регионов
    if 'Name' not in df.columns:
        st.error(f"Ошибка: в файле {file_name} отсутствует столбец 'Name'")
        st.stop()  # Останавливаем приложение при критической ошибке
    
    # Очищаем названия регионов от лишних пробелов
    df['Name'] = df['Name'].str.strip()
    
    return df

# --- Основная часть приложения ---

# Заголовок дашборда
st.title('📊 Региональный анализ данных')

# Информационное сообщение о загрузке
with st.spinner('Загрузка данных...'):
    try:
        # Загружаем все три набора данных
        budget_df = load_data('budget.csv')  # Данные по бюджетам
        housing_df = load_data('housing.csv')  # Данные по жилому фонду
        investments_df = load_data('investments.csv')  # Инвестиционные данные
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        st.stop()  # Останавливаем приложение при ошибке

# Раздел выбора темы для анализа
st.header('1. Выбор темы анализа')
topic = st.radio(
    "Выберите тему данных для анализа:",
    ('Бюджет', 'Жилищный фонд', 'Инвестиции'),
    horizontal=True,  # Располагаем кнопки горизонтально
    index=0  # Выбираем первый вариант по умолчанию
)

# Выбираем соответствующий набор данных и подпись для оси Y
if topic == 'Бюджет':
    df = budget_df
    y_label = 'Бюджет (рубли)'
    description = "Анализ бюджетных показателей регионов"
elif topic == 'Жилищный фонд':
    df = housing_df
    y_label = 'Жилищный фонд (кв. м на чел.)'
    description = "Анализ обеспеченности жильем по регионам"
else:
    df = investments_df
    y_label = 'Инвестиции (рубли)'
    description = "Анализ инвестиционных потоков по регионам"

# Выводим описание выбранной темы
st.caption(f"🔍 {description}")

# Раздел выбора временного периода
st.header('2. Выбор периода анализа')

# Находим все числовые столбцы (годы) в данных
numeric_cols = [col for col in df.columns if str(col).isdigit()]
if not numeric_cols:
    st.error("Ошибка: в данных отсутствуют числовые столбцы (годы).")
    st.stop()

# Определяем минимальный и максимальный год
available_years = [int(col) for col in numeric_cols]
min_year, max_year = min(available_years), max(available_years)

# Слайдер для выбора диапазона лет
year_range = st.slider(
    'Выберите диапазон лет для анализа:',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),  # Значения по умолчанию
    help="Перемещайте ползунки для выбора нужного периода"
)

# Формируем список выбранных годов
year_columns = [str(year) for year in range(year_range[0], year_range[1]+1)]

# Раздел выбора регионов
st.header('3. Выбор регионов')

# Получаем список всех регионов из данных
all_regions = df['Name'].unique()

# Мультиселект для выбора регионов
selected_regions = st.multiselect(
    'Выберите регионы для сравнения:',
    options=all_regions,
    default=[all_regions[0]],  # По умолчанию выбираем первый регион
    help="Можно выбрать несколько регионов для сравнения"
)

# Проверяем, что выбран хотя бы один регион
if not selected_regions:
    st.warning("⚠️ Пожалуйста, выберите хотя бы один регион.")
    st.stop()

# Фильтруем данные по выбранным регионам
filtered_df = df[df['Name'].isin(selected_regions)][['Name'] + year_columns]

# --- Визуализация данных ---
st.header('4. Визуализация данных')

# Создаем график с настройками
fig, ax = plt.subplots(figsize=(12, 6))  # Задаем размер графика

# Используем предопределенные цвета для графиков
colors = list(mcolors.TABLEAU_COLORS.values())

# Строим линии для каждого региона
for idx, (_, row) in enumerate(filtered_df.iterrows()):
    region_name = row['Name']  # Название региона
    values = row[year_columns].values  # Значения показателя
    years = [int(year) for year in year_columns]  # Годы
    
    # Рисуем линию для региона
    ax.plot(
        years,
        values,
        label=region_name,
        color=colors[idx % len(colors)],  # Циклически используем цвета
        marker='o',  # Добавляем точки на график
        linewidth=2  # Толщина линии
    )

# Настройки внешнего вида графика
ax.set_xlabel('Год', fontsize=12)
ax.set_ylabel(y_label, fontsize=12)
ax.set_title(f'Динамика показателя "{topic}" по выбранным регионам', fontsize=14)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # Выносим легенду за график
ax.grid(True, linestyle='--', alpha=0.7)  # Добавляем сетку
plt.xticks(years, rotation=45)  # Поворачиваем подписи на оси X
plt.tight_layout()  # Оптимизируем расположение элементов

# Выводим график в Streamlit
st.pyplot(fig)

# --- Таблица с данными ---
st.header('5. Таблица данных')

# Настраиваем отображение таблицы
st.dataframe(
    filtered_df.reset_index(drop=True),
    height=min(400, len(filtered_df) * 35 + 35),  # Автоматическая высота
    use_container_width=True,  # Используем всю ширину контейнера
    hide_index=True  # Скрываем индексы
)

# --- Дополнительная информация ---
st.markdown("---")
st.info(f"""
**Сводная информация:**
- Анализируемый показатель: {topic}
- Период: с {year_range[0]} по {year_range[1]} год
- Количество регионов: {len(selected_regions)}
- Последнее обновление данных: {pd.Timestamp.now().strftime('%Y-%m-%d')}
""")

# Секция для отладки (можно закомментировать в продакшене)
with st.expander("Техническая информация (для отладки)"):
    st.write("Определенная кодировка файлов:")
    for file in ['budget.csv', 'housing.csv', 'investments.csv']:
        with open(file, 'rb') as f:
            st.write(f"{file}: {chardet.detect(f.read(10000))['encoding']}")