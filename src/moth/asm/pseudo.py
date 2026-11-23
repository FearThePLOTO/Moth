def _split(ops, n):
    """this func takes the text of operands and divide it into a list like
    "$t0, $t1" => ["$t0", "$t1"]"""
    if ops.strip() == "":
        lis = []
    else:
        lis = [x.strip() for x in ops.split(",")]

    if len(lis) != n or "" in lis:
        raise ValueError(f"expected {n} operands, got {len(lis)}")
    return lis


def _imm(text):
    """this func converts text to number whatever its decimal or hexa"""
    try:
        return int(text, 0)
    except ValueError as err:
        raise ValueError(f'"{text}" is not a number') from err


def _fits16(immd):
    return -32768 <= immd <= 32767


def _fits_u16(immd):
    return 0 <= immd <= 65535


def _li_words(immd):
    """this func decide the number of words 1 or 2 and
    check the size of the number is not bigger than 32 bit"""
    if not -(2**31) <= immd <= 2**32 - 1:
        raise ValueError(f"immediate {immd} does not fit in 32 bits")

    return 1 if _fits16(immd) or _fits_u16(immd) else 2


def expand(m, ops, symbols):
    if m == "nop":
        _split(ops, 0)

        return [("sll", "$zero, $zero, 0")]

    if m == "move":
        rd, rs = _split(ops, 2)

        return [("addu", f"{rd}, $zero, {rs}")]

    if m == "li":
        rt, immd_text = _split(ops, 2)

        immd = _imm(immd_text)

        words = _li_words(immd)

        if words == 1:
            if _fits16(immd):
                return [("addiu", f"{rt}, $zero, {immd}")]
            else:
                return [("ori", f"{rt}, $zero, {immd}")]

        return [("lui", f"$at, {(immd >> 16) & 0xFFFF}"), ("ori", f"{rt}, $at, {immd & 0xFFFF}")]

    if m == "la":
        rt, label = _split(ops, 2)
        if label not in symbols:
            raise ValueError(f'undefined label "{label}"')
        addrs = symbols[label]
        return [("lui", f"$at, {(addrs >> 16) & 0xFFFF}"), ("ori", f"{rt}, $at, {addrs & 0xFFFF}")]

    return None
