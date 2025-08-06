import re
import os
import csv
import argparse

# =============================================================================
# Convert
# =============================================================================
import zipfile
import html2text
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def convert_epub(epub_file, output):
    if not os.path.isfile(epub_file):
        print(f"Not found: {epub_file}")
        return
    
    temp_dir = os.path.join(os.path.dirname(output), f"temp_epub_{os.getpid()}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(epub_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        container_path = os.path.join(temp_dir, 'META-INF', 'container.xml')
        if not os.path.isfile(container_path):
            raise FileNotFoundError("EPUB格式错误: 缺少container.xml")
        
        container_tree = ET.parse(container_path)
        rootfile = container_tree.find('.//{*}rootfile')
        content_path = os.path.join(temp_dir, rootfile.attrib['full-path'])
        
        # 解析内容文件(opf)找到所有章节
        content_dir = os.path.dirname(content_path)
        content_tree = ET.parse(content_path)
        manifest = content_tree.find('.//{*}manifest')
        
        # 收集所有HTML内容文件
        html_files = []
        for item in manifest.findall('{*}item'):
            if item.attrib.get('media-type') in ['application/xhtml+xml', 'text/html']:
                file_path = os.path.join(content_dir, item.attrib['href'])
                if os.path.isfile(file_path):
                    html_files.append(file_path)
        
        # 按顺序处理所有HTML文件并提取文本
        all_text = []
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = False  # 保留斜体/粗体标记
        h.body_width = 0  # 禁用换行
        
        for html_file in html_files:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 清理HTML并转换为Markdown文本
            soup = BeautifulSoup(html_content, 'html.parser')
            clean_html = str(soup)
            text = h.handle(clean_html)
            
            # 进一步清理文本
            text = re.sub(r'\n{3,}', '\n\n', text)  # 减少多余空行
            text = re.sub(r' +', ' ', text)         # 减少多余空格
            text = text.strip()
            
            if text:
                all_text.append(text)
        
        # 合并所有文本并保存
        full_text = '\n\n'.join(all_text)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        return output
    
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

# =============================================================================
# Dump Words
# =============================================================================
from collections import defaultdict
from stardict import StarDict

def count_words_in_file(file_path):
    """
    统计文本文件中每个单词的出现次数
    
    :param file_path: 文本文件的路径
    :return: 包含单词计数的字典
    """
    # 使用默认字典自动初始化计数为0
    word_count = defaultdict(int)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # 移除行尾换行符并转换为小写
                clean_line = line.strip().lower()
                if not clean_line:
                    continue
                
                # 使用正则表达式分割单词（处理标点符号）
                words = re.findall(r'\b[a-zA-Z\']+\b', clean_line)
                
                for word in words:
                    word_count[word] += 1
                    
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 不存在")
        return {}
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return {}
    
    return dict(word_count)

def dump_words(txt_file, output, with_chinese, blacklist):
    if with_chinese:
        db = os.path.join(os.path.dirname(__file__), 'dict.db')
        sd = StarDict(db, False)

    word_counts = count_words_in_file(txt_file)
    sorted_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    with open(output, 'w', encoding='utf-8') as file:
        file.write(f'word,count,chinese\n')
        for word, count in sorted_counts:
            if len(word) == 1 or word in blacklist:
                continue
            chinese = ''
            if with_chinese:
                w = sd.query(word)
                chinese = word if w is None else w['translation'].lstrip().replace(',', '，').replace('\n','; ')
            file.write(f'{word},{count},{chinese}\n')

def load_blacklist(blacklist_file):
    blacklist = set()
    if blacklist_file is not None:
        with open(blacklist_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  
            for row in reader:
                blacklist.add(row[0])
    return blacklist

def main():
    parser = argparse.ArgumentParser(description="文本词频分析工具")
    parser.add_argument('-i', '--input', required=True, help="输入文件路径")
    parser.add_argument('-o', '--output', help="输出文件路径")
    parser.add_argument('-c', '--chinese', action='store_true', help="输出中文释义")
    parser.add_argument('-b', '--blacklist', help="黑名单文件路径")
    
    args = parser.parse_args()
    input_file = args.input
    output_file = args.output
    blacklist_file = args.blacklist
    with_chinese = False if args.chinese is None else True

    print(f'input_file: {input_file}')
    print(f'output_file: {output_file}')
    print(f'blacklist_file: {blacklist_file}')
    print(f'with_chinese: {with_chinese}')

    try:
        ext = os.path.splitext(input_file)[1]
        if ext == '.txt':
            blacklist = load_blacklist(blacklist_file)
            if output_file is None:
                output_file = os.path.splitext(input_file)[0] + '.bookwords.csv'
            dump_words(input_file, output_file, with_chinese, blacklist)
            print(f"Dump Success: {output_file}")
        elif ext == '.epub':
            if output_file is None:
                output_file = os.path.splitext(input_file)[0] + '.txt'
            convert_epub(input_file, output_file)
            print(f"Convert Success: {output_file}")
        else:
            raise Exception(f'Not Support: {input_file}, Please input .TXT or .EPUB')
    except Exception as ex:
        print(f'Failed: {ex}')

if __name__ == "__main__":
    main()