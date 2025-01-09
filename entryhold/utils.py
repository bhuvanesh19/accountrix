def case_convert(s):
    ret = s[0].lower()
    for i in range(1, len(s)):
        if s[i].isupper():
            ret += "_"
        ret += s[i].lower()
    return ret
