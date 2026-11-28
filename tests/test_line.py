from moth.asm.line import extract_label, parse_line, parse_lines, remove_comment


def test_remove_comment_keeps_hash_inside_strings():
    assert remove_comment('li $t0, "#" # hi') == ('li $t0, "#" ', "hi")
    assert remove_comment("add $t0, $t1, $t2") == ("add $t0, $t1, $t2", None)


def test_extract_label_handles_colons_in_strings():
    assert extract_label('msg: .asciiz "a:b"') == ("msg", '.asciiz "a:b"')
    assert extract_label('    .asciiz "a:b"') == (None, '.asciiz "a:b"')


def test_parse_line_with_tabs_and_comment():
    line = parse_line("\tadd\t$t0, $t1, $t2 # ok", 4)
    assert line.line_number == 4
    assert line.mnemonic == "add"
    assert line.operands == "$t0, $t1, $t2"
    assert line.comment == "ok"


def test_parse_lines_handles_bom_and_crlf():
    lines = parse_lines("\ufeff.text\r\nmain:\r\n\tnop\r\n")
    assert [line.mnemonic for line in lines] == [".text", None, "nop"]
    assert lines[2].line_number == 3
