import os
import sys

def count_effective_lines(file_path):
    """
    统计代码文件的有效行数（排除空行和注释行）
    
    Args:
        file_path (str): 要统计的代码文件路径
        
    Returns:
        tuple: (总行数, 空行数, 注释行数, 有效代码行数)
    """
    total_lines = 0
    empty_lines = 0
    comment_lines = 0
    code_lines = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                total_lines += 1
                stripped_line = line.strip()
                
                # 统计空行
                if not stripped_line:
                    empty_lines += 1
                    continue
                
                # 统计注释行
                if stripped_line.startswith('#'):
                    comment_lines += 1
                    continue
                
                # 统计代码行
                code_lines += 1
                
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return None
    except Exception as e:
        print(f"错误：读取文件时发生错误 - {str(e)}")
        return None
    
    return total_lines, empty_lines, comment_lines, code_lines

def main():
    if len(sys.argv) != 2:
        print("用法：python count_lines.py <文件路径>")
        return
    
    file_path = sys.argv[1]
    result = count_effective_lines(file_path)
    
    if result:
        total, empty, comment, code = result
        print(f"\n文件统计结果：{os.path.basename(file_path)}")
        print("-" * 40)
        print(f"总行数：{total}")
        print(f"空行数：{empty}")
        print(f"注释行数：{comment}")
        print(f"有效代码行数：{code}")
        print("-" * 40)
        print(f"代码占比：{(code/total)*100:.1f}%")

if __name__ == "__main__":
    main() 