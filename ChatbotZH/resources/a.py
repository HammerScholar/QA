file_conf_name = 'conf_name.txt'
file_conf_category = 'conf_category.txt'
file_journal_name = 'journal_name.txt'
file_journal_category = 'journal_category.txt'

def a(file):
    with open(file, 'r') as f:
        tasks = f.read().replace('- ', '').split('\n')
    
    for i in range(len(tasks)):
        for j in range(i+1, len(tasks)):
            if tasks[i] in tasks[j]:
                temp = tasks[i]
                tasks[i] = tasks[j]
                tasks[j] = temp

    result = ''
    for i in tasks:
        result += '- ' + i + '\n'
    
    with open(file, 'w') as f:
        f.write(result)

if __name__ == '__main__':
    # a(file_conf_name)
    # a(file_conf_category)
    a(file_journal_name)
    # a(file_journal_category)