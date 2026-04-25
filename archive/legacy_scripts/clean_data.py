import os
import re

def clean_csv_files(root_dir):
    csv_pattern = re.compile(r'.*\.csv$', re.IGNORECASE)
    
    file_count = 0
    cleaned_folders = set()
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if csv_pattern.match(file):
                file_path = os.path.join(root, file)
                # print(f"Cleaning {file_path}...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                cleaned_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('#'):
                        continue
                    
                    parts = stripped_line.split(',')
                    if len(parts) >= 9:
                        new_parts = parts[:8] + ['']
                        cleaned_lines.append(','.join(new_parts) + '\n')
                    else:
                        cleaned_lines.append(line)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                
                file_count += 1
                cleaned_folders.add(root)

    print(f"Total CSV files cleaned: {file_count}")
    print("Folders processed:")
    for folder in sorted(cleaned_folders):
        print(f"  - {folder}")

if __name__ == "__main__":
    results_dir = r'c:\Users\ian\Desktop\PROJECT\cs525_advanced_distributed_systems\data\results'
    clean_csv_files(results_dir)
    print("Cleanup complete.")
