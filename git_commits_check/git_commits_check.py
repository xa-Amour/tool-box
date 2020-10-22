import xlwt

commit_id_lst = []
commit_content = []
commit_author = []


def commits_parser(file):
    with open(file, 'r', encoding='utf-8') as file_object:
        lines = file_object.readlines()
        for (line_number, line_content) in enumerate(lines):
            if line_content.startswith("commit"):
                commit_id_lst.append(line_content[7:14])
                if (line_number - 2) > 0:
                    commit_content.append(lines[line_number - 2])
                while (line_number - 5) > 0:
                    if lines[line_number - 5].strip().startswith("Author: "):
                        commit_author.append(lines[line_number - 5].strip()[7::])
                        break
                    line_number -= 1


def set_style(name, height, bold=False):
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


def gen_commits_excel(input, output):
    commits_parser(input)
    f = xlwt.Workbook()
    sheet = f.add_sheet('students', cell_overwrite_ok=True)
    xls_title = ["Commit", "Title", "Owner", "Status"]
    for i in range(0, len(xls_title)):
        sheet.write(0, i, xls_title[i], set_style('Times New Roman', 220, True))
    for i in range(len(commit_id_lst)):
        sheet.write(i + 1, 0, commit_id_lst[i])
    for i in range(len(commit_content)):
        sheet.write(i + 1, 1, commit_content[i])
    for i in range(len(commit_author)):
        sheet.write(i + 1, 2, commit_author[i])
    f.save(output)


def main():
    gen_commits_excel("placeholder_commits_log", "placeholder_commits_log.xls")


if __name__ == '__main__':
    main()
