## BookWords

用于分析文本中的英文单词并输出词频列表

### 如何使用

如果需要输出带有中文释义的词频列表，需要先把 `dict.db` 解压到项目根目录

```bash
# 将 epub 文件转换为 txt 文件
./bookwords.py -t /path/to/epub_file -o /output/txt_file

# 分析 txt 文件并生成词频列表
./bookwords.py -i /path/to/txt_file -o /output/csv_file

# 输出带有中文释义的词频列表
./bookwords.py -i /path/to/txt_file -o /output/csv_file -c

# 使用黑名单过滤
./bookwords.py -i /path/to/txt_file -b /path/to/blacklist_file
```

### 输出示例

词频列表输出为 csv 格式：

```
word,count,chinese
the,1487,art. 那
to,1053,prep. 到， 向， 趋于 | adv. 向前
and,1007,conj. 和， 与 | [计] 与
of,801,prep. 的， 属于
her,712,pron. 她的， 她
was,689,be的过去式
my,579,pron. 我的 | [医] 迈尔(热容单位)
```

### 注意事项

1. 默认忽略单个字母的单词，例如：a

### 鸣谢

离线词典：[skywind3000/ECDICT](https://github.com/skywind3000/ECDICT)