import base64
from PIL import Image
import io
import os
import re
import json
import glob

def detect_file_format(content):
    """
    Определяет формат файла с полосками
    """
    content = content.strip()
    
    # Проверяем JSON
    if content.startswith('[') and content.endswith(']'):
        return 'json'
    # Проверяем, что это просто список base64 строк
    elif 'data:image' in content or len(content.split('\n')) > 1:
        return 'lines'
    else:
        return 'unknown'

def load_strips_from_file(filename):
    """
    Загружает полоски из файла в любом формате
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        format_type = detect_file_format(content)
        
        if format_type == 'json':
            data = json.loads(content)
            return data
        else:  # lines format
            lines = content.split('\n')
            return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"❌ Ошибка чтения файла {filename}: {e}")
        return []

def combine_image_strips(input_file, output_path):
    """
    Универсальная функция для сборки изображения из полосок
    """
    
    # Загружаем полоски
    base64_strips = load_strips_from_file(input_file)
    
    if not base64_strips:
        print(f"❌ В файле {input_file} нет данных или ошибка чтения")
        return None
    
    print(f"📁 Файл: {os.path.basename(input_file)}")
    print(f"📊 Найдено {len(base64_strips)} полосок")
    
    images = []
    
    # Обрабатываем каждую полоску
    for i, strip in enumerate(base64_strips):
        try:
            # Убираем префикс data URL
            if strip.startswith('data:image'):
                strip = strip.split(',')[1]
            
            # Декодируем base64
            image_data = base64.b64decode(strip)
            image = Image.open(io.BytesIO(image_data))
            images.append(image)
            print(f"  ✅ Полоска {i+1}: {image.size[0]}x{image.size[1]}")
            
        except Exception as e:
            print(f"  ❌ Ошибка в полоске {i+1}: {e}")
            continue
    
    if not images:
        print(f"  ❌ Не удалось загрузить ни одной полоски из {input_file}")
        return None
    
    # Собираем изображение
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    
    print(f"  📐 Итоговый размер: {max_width}x{total_height}")
    
    combined_image = Image.new('RGB', (max_width, total_height))
    
    current_y = 0
    for img in images:
        combined_image.paste(img, (0, current_y))
        current_y += img.height
    
    # Сохраняем
    combined_image.save(output_path, quality=95)
    print(f"  💾 Изображение сохранено: {output_path}")
    print(f"  🎯 Размер: {combined_image.size}")
    print("  " + "="*50)
    
    return combined_image

def process_directory(input_dir="input", output_dir="output", file_pattern="*.txt"):
    """
    Обрабатывает все файлы в указанной папке
    
    Args:
        input_dir: папка с исходными файлами
        output_dir: папка для сохранения результатов
        file_pattern: шаблон для поиска файлов (например, "*.txt" или "*.json")
    """
    
    # Создаем папки если их нет
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Ищем файлы по шаблону
    search_pattern = os.path.join(input_dir, file_pattern)
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"❌ Файлы по шаблону '{search_pattern}' не найдены")
        print("📁 Поместите файлы с полосками в папку 'input'")
        return
    
    print(f"🔍 Найдено файлов для обработки: {len(files)}")
    print("=" * 60)
    
    processed_count = 0
    failed_count = 0
    
    for file_path in files:
        try:
            # Создаем имя для выходного файла
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}.jpg")
            
            # Обрабатываем файл
            result = combine_image_strips(file_path, output_path)
            
            if result:
                processed_count += 1
            else:
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Критическая ошибка при обработке {file_path}: {e}")
            failed_count += 1
            continue
    
    print("=" * 60)
    print(f"📊 ИТОГ:")
    print(f"✅ Успешно обработано: {processed_count}")
    print(f"❌ Не удалось обработать: {failed_count}")
    print(f"📁 Результаты сохранены в папке: {output_dir}")

def process_single_file(input_file, output_dir="output"):
    """
    Обрабатывает один конкретный файл
    """
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_path = os.path.join(output_dir, f"combined_{base_name}.jpg")
    
    return combine_image_strips(input_file, output_path)

# Основная функция
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Сборка изображений из base64 полосок')
    parser.add_argument('--input', '-i', default="input", 
                       help='Папка с исходными файлами (по умолчанию: input)')
    parser.add_argument('--output', '-o', default="output", 
                       help='Папка для сохранения результатов (по умолчанию: output)')
    parser.add_argument('--pattern', '-p', default="*.txt", 
                       help='Шаблон поиска файлов (по умолчанию: *.txt)')
    parser.add_argument('--file', '-f', 
                       help='Обработать один конкретный файл')
    
    args = parser.parse_args()
    
    if args.file:
        # Обработка одного файла
        print(f"🎯 Обработка одного файла: {args.file}")
        process_single_file(args.file, args.output)
    else:
        # Обработка всей папки
        print(f"📁 Обработка папки: {args.input}")
        print(f"🔍 Шаблон поиска: {args.pattern}")
        print(f"💾 Папка для результатов: {args.output}")
        print("=" * 60)
        
        process_directory(args.input, args.output, args.pattern)