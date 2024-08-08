import os
import git
from googletrans import Translator
import argparse

lang_codes = {
    'zh-Hans': 'zh-cn',
    'zh-Hant': 'zh-tw',
    'en': 'en'
}

def translate_strings(strings, target_lang):
    translator = Translator()
    translations = {}
    print(f"===========\ntranslating from en to {target_lang}")
    for key, en_string in strings.items():
        translation = translator.translate(en_string, dest=target_lang).text
        translations[key] = translation
    return translations

def write_translations(base_file_path, file_path, base_strings, target_strings, translations):
    print(f"===========\nwriting to file: {file_path}, {len(base_strings)}/{len(translations)}")
    
    with open(base_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            line = line.strip()
            if line.startswith('/*') or line.startswith('//') or line == '':
                file.write(line + '\n')
            elif '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().strip('"')
                if key in translations:
                    file.write(f'"{key}" = "{translations[key]}";')
                    print(f'writing translated "{key}" = "{translations[key]}";')
                elif key in target_strings:
                    file.write(f'"{key}" = "{target_strings[key]}";')
                file.write('\n')

def find_localizable_files(root_dir):
    localizable_files = {}
    print(f"Searching for localization files in: {root_dir}")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        print(dirpath)
        if dirpath.endswith('.lproj'):
            lang = os.path.basename(dirpath).split('.')[0]
            for filename in filenames:
                if filename == 'Localizable.strings':
                    file_path = os.path.join(dirpath, filename)
                    localizable_files[lang] = file_path
                    print(f"Added {lang} localization file: {file_path}")
    print(f"Total localization files found: {len(localizable_files)}")
    return localizable_files

def parse_strings_file(file_path):
    strings = {}
    print(f"Parsing file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().strip('"')
                value = value.strip().strip(';').strip('"')
                strings[key] = value
    print(f"Parsed {len(strings)} strings from the file")
    return strings

def find_missing_strings(base_strings, target_strings):
    missing = {k: v for k, v in base_strings.items() if k not in target_strings}
    print(f"Found {len(missing)} missing strings")
    return missing
    
def translate_and_write(base_file_path, base_strings_new, mapped_lang, file_path, additional_strings):
    print(f"\nProcessing {mapped_lang} localization")
    target_strings = parse_strings_file(file_path)
    missing_strings = find_missing_strings(base_strings_new, target_strings)
    strings_to_translate = {**missing_strings, **additional_strings}

    if strings_to_translate:
        print(f"\nStrings to translate for {mapped_lang}:")
        for key, value in strings_to_translate.items():
            print(f'"{key}" = "{value}";')

        translated_strings = translate_strings(strings_to_translate, mapped_lang)
        print(f"\nTranslated strings for {mapped_lang}:")
        for key, value in translated_strings.items():
            print(f'"{key}" = "{value}";')

        write_translations(base_file_path, file_path, base_strings_new, target_strings, translated_strings)
        print(f"Translations written to {file_path}")
    else:
        print(f"No strings to translate for {mapped_lang}")

def autotranslate(old_commit_id, new_commit_id):
    root_dir = os.path.join(os.getcwd(), "")
    repo = git.Repo(root_dir)
    
    if not new_commit_id:
        new_commit_id = repo.head.commit

    print(f'Previous value: {old_commit_id}')
    print(f'Target value: {new_commit_id}')

    # Checkout the old commit
    if old_commit_id:
        repo.git.checkout(old_commit_id)
    #    root_dir = os.path.join(temp_dir, "")
        localizable_files = find_localizable_files(root_dir)

        if not localizable_files:
            print("No localization files found. Please check the directory structure.")
            return

        print("\nAvailable language files:")
        for lang, path in localizable_files.items():
            print(f"{lang}: {path}")

        # Find the English file (it could be 'en', 'en-US', 'en-GB', etc.)
        en_key = next((lang for lang in localizable_files.keys() if lang.startswith('en')), None)

        if not en_key:
            print("Error: English localization file not found.")
            print("Available languages:", ", ".join(localizable_files.keys()))
            return

        print(f"\nUsing {en_key} as the base language")
        base_strings_old = parse_strings_file(localizable_files[en_key])

    # Checkout the new commit
    repo.git.checkout(new_commit_id, b='temp-localization-updates')

    localizable_files = find_localizable_files(root_dir)
    # Find the English file (it could be 'en', 'en-US', 'en-GB', etc.)
    en_key = next((lang for lang in localizable_files.keys() if lang.startswith('en')), None)

    if not en_key:
        print("Error: English localization file not found.")
        print("Available languages:", ", ".join(localizable_files.keys()))
        return

    base_strings_new = parse_strings_file(localizable_files[en_key])

    # Find the diff between the old and new base strings
    if old_commit_id:
        diff_strings = {k: v for k, v in base_strings_new.items() if k in base_strings_old and base_strings_new[k] != base_strings_old[k]}
        print(f"Found {len(diff_strings)} modified strings in the base language")
    else:
        diff_strings = {}

    for lang, file_path in localizable_files.items():
        mapped_lang = lang_codes.get(lang, lang)
        if mapped_lang.startswith('en'):
            continue
        translate_and_write(localizable_files[en_key], base_strings_new, mapped_lang, file_path, diff_strings)
    
def checkCN():
    # 找到 cn
    root_dir = os.path.join(os.getcwd(), "")
    
    # 找到 en
    translate_and_write(localizable_files[en_key], base_strings_new, mapped_lang, file_path, diff_strings)

def main():
    # 创建一个ArgumentParser对象
    parser = argparse.ArgumentParser(description='Process some arguments.')

    # 添加两个命令行参数
#    parser.add_argument('--prev', type=str, help='The previous value')
#    parser.add_argument('--target', type=str, help='The target value')
    parser.add_argument('--prev', nargs='?', const='', help='The previous value')
    parser.add_argument('--target', nargs='?', const='', help='The target value')

    parser.add_argument('pre', nargs='?', const='', help='Pre check CN')

    # 解析命令行参数
    args = parser.parse_args()
    
    pre = args.pre
    
    if pre:
        checkCN()
    else:
        # 访问参数值
        old_commit_id = args.prev
        new_commit_id = args.target
        
        autotranslate(old_commit_id, new_commit_id)
    
    
if __name__ == "__main__":
    main()
