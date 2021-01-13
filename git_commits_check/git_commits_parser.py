import xlwt

CMT_ID, CMT_CONT, CMT_AUTH = [], [], []


def parse_cmts_fairly(cmts):
    with open(cmts, 'r', encoding='utf-8') as fr:
        lines, inner_auths = fr.readlines(), []
        for (line_num, line_cont) in enumerate(lines):
            if line_cont.startswith("commit"):
                CMT_ID.append(line_cont[7:14])
                if (line_num - 2) > 0:
                    CMT_CONT.append(lines[line_num - 2])
                if inner_auths != []:
                    max_label = max(
                        inner_auths,
                        key=inner_auths.count)
                    inner_auths = []
                    CMT_AUTH.append(max_label)
            if line_cont.startswith("    Author:"):
                inner_auth = str(line_cont.strip()[7::])
                inner_auths.append(inner_auth)


def parse_cmts_loosely(cmts):
    with open(cmts, 'r', encoding='utf-8') as fr:
        lines = fr.readlines()
        for (line_num, line_cont) in enumerate(lines):
            if line_cont.startswith("commit"):
                CMT_ID.append(line_cont[7:14])
                if (line_num - 2) > 0:
                    CMT_CONT.append(lines[line_num - 2])
                while (line_num - 5) > 0:
                    if lines[line_num - 5].strip().startswith("Author: "):
                        CMT_AUTH.append(
                            lines[line_num - 5].strip()[7::])
                        break
                    line_num -= 1


def set_style(name, height, bold=False):
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


def gen_cmts_excl(cmts, excl):
    parse_cmts_loosely(cmts)
    f = xlwt.Workbook()
    sheet = f.add_sheet('parser', cell_overwrite_ok=True)
    xls_title = ["Commit", "Title", "Owner", "Status"]
    for i in range(0, len(xls_title)):
        sheet.write(
            0, i, xls_title[i], set_style(
                'Times New Roman', 220, True))
    CMT_ID.pop()
    for i in range(len(CMT_ID)):
        sheet.write(i + 1, 0, CMT_ID[i])
    for i in range(len(CMT_CONT)):
        sheet.write(i + 1, 1, CMT_CONT[i])
    for i in range(len(CMT_AUTH)):
        sheet.write(i + 1, 2, CMT_AUTH[i])
    f.save(excl)


def main():
    gen_cmts_excl(
        "placeholder_commits_log",
        "placeholder_commits_log.xls")


if __name__ == '__main__':
    main()
